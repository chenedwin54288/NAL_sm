#!/usr/bin/env python3

import argparse
import csv
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TRUNCATED_PCAP_MARKERS = (
    "appears to have been cut short",
    "cut short in the middle of a packet",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract TCP window size samples from a pcap and plot them over time."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=str(BASE_DIR / "capture_test.pcap"),
        help="Path to the pcap file (default: capture_test.pcap)",
    )
    parser.add_argument("--src-ip", help="Only include packets from this source IPv4 address")
    parser.add_argument("--src-port", type=int, help="Only include packets from this source port")
    parser.add_argument(
        "--dst-ip", help="Only include packets to this destination IPv4 address"
    )
    parser.add_argument("--dst-port", type=int, help="Only include packets to this destination port")
    parser.add_argument(
        "--raw-window",
        action="store_true",
        help="Use the raw TCP header window value instead of the scaled window size",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output image path (default: outputs/window_size_<filters>.png)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the graph interactively in addition to saving it",
    )
    return parser.parse_args()


def build_display_name(args: argparse.Namespace) -> str:
    parts = []
    if args.src_ip:
        parts.append(f"src_{args.src_ip.replace('.', '_')}")
    if args.src_port is not None:
        parts.append(f"sport_{args.src_port}")
    if args.dst_ip:
        parts.append(f"dst_{args.dst_ip.replace('.', '_')}")
    if args.dst_port is not None:
        parts.append(f"dport_{args.dst_port}")
    if not parts:
        parts.append("all_tcp")
    return "_".join(parts)


def build_tshark_filter(args: argparse.Namespace) -> str:
    filters = ["tcp"]
    if args.src_ip:
        filters.append(f"ip.src == {args.src_ip}")
    if args.src_port is not None:
        filters.append(f"tcp.srcport == {args.src_port}")
    if args.dst_ip:
        filters.append(f"ip.dst == {args.dst_ip}")
    if args.dst_port is not None:
        filters.append(f"tcp.dstport == {args.dst_port}")
    return " and ".join(filters)


def extract_samples(pcap_path: Path, args: argparse.Namespace, log_path: Path):
    window_field = "tcp.window_size_value" if args.raw_window else "tcp.window_size"
    tshark_cmd = [
        "tshark",
        "-r",
        str(pcap_path),
        "-Y",
        build_tshark_filter(args),
        "-T",
        "fields",
        "-E",
        "separator=\t",
        "-e",
        "frame.time_relative",
        "-e",
        "ip.src",
        "-e",
        "tcp.srcport",
        "-e",
        "ip.dst",
        "-e",
        "tcp.dstport",
        "-e",
        window_field,
        "-e",
        "tcp.window_size_value",
    ]

    try:
        process = subprocess.Popen(
            tshark_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        print("tshark is required but was not found in PATH.", file=sys.stderr)
        return None

    timestamps = []
    windows = []
    first_timestamp = None

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", newline="") as log_file:
        writer = csv.writer(log_file, delimiter="\t")
        writer.writerow(
            ["time_s", "src_ip", "src_port", "dst_ip", "dst_port", "window_size"]
        )

        assert process.stdout is not None
        for line in process.stdout:
            if not line.strip():
                continue

            parts = line.split("\t")
            if len(parts) < 7:
                continue

            time_s, src_ip, src_port, dst_ip, dst_port, scaled_window, raw_window = parts[:7]
            window_value = scaled_window if scaled_window else raw_window
            if not window_value:
                continue

            try:
                timestamp = float(time_s)
                window = int(window_value)
            except ValueError:
                continue

            if first_timestamp is None:
                first_timestamp = timestamp

            timestamps.append(timestamp - first_timestamp)
            windows.append(window)
            writer.writerow(
                [f"{timestamp - first_timestamp:.9f}", src_ip, src_port, dst_ip, dst_port, window]
            )

    stderr_output = ""
    if process.stderr is not None:
        stderr_output = process.stderr.read().strip()

    return_code = process.wait()
    if return_code != 0:
        lowered_stderr = stderr_output.lower()
        truncated_pcap = any(marker in lowered_stderr for marker in TRUNCATED_PCAP_MARKERS)
        if truncated_pcap and windows:
            print(
                "Warning: pcap appears truncated; plotted the samples tshark could still read.",
                file=sys.stderr,
            )
            return timestamps, windows

        print(
            f"Failed to read pcap with tshark: {stderr_output or 'Unknown tshark error'}",
            file=sys.stderr,
        )
        return None

    return timestamps, windows


def build_plot(timestamps, windows, title: str, output_path: Path, show: bool):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
    except ImportError:
        print(
            "matplotlib is required to build the graph. Install it with: pip install matplotlib",
            file=sys.stderr,
        )
        return 1

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(timestamps, windows, color="steelblue", linewidth=1.5, alpha=0.9)
    ax.scatter(timestamps, windows, color="navy", s=10, alpha=0.7)

    ax.set_title(title)
    ax.set_xlabel("Time since first sample (s)")
    ax.set_ylabel("Window size (bytes)")
    ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{int(value)}"))
    ax.grid(True, linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close(fig)

    return 0


def main() -> int:
    args = parse_args()
    pcap_path = Path(args.input)
    if not pcap_path.is_absolute():
        pcap_path = BASE_DIR / pcap_path

    if not pcap_path.exists():
        print(f"Input pcap file not found: {pcap_path}", file=sys.stderr)
        return 1

    base_name = build_display_name(args)
    output_path = Path(args.output) if args.output else BASE_DIR / f"outputs/window_size_{base_name}.png"
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log_path = output_path.with_suffix(".tsv")
    samples = extract_samples(pcap_path, args, log_path)
    if samples is None:
        return 1

    timestamps, windows = samples
    if not windows:
        print("No matching TCP packets with window size were found.", file=sys.stderr)
        return 1

    title_suffix = base_name.replace("_", " ")
    rc = build_plot(timestamps, windows, f"TCP Window Size over Time ({title_suffix})", output_path, args.show)
    if rc != 0:
        return rc

    print(f"Saved graph with {len(windows)} samples to {output_path}")
    print(f"Saved extracted samples to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
