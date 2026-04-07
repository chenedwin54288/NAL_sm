#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path


LOG_PATTERN = re.compile(
    r"""
    ^\[\s*(?P<timestamp>\d+\.\d+)\]      # kernel log timestamp
    .*?cwnd=(?P<cwnd>\d+)                # congestion window value
    .*?Destination:\s+
    (?P<ip>\d{1,3}(?:\.\d{1,3}){3})      # destination IPv4
    :(?P<port>\d+)                       # destination port
    \s*$
    """,
    re.VERBOSE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract cwnd samples for a destination IP:port and plot them."
    )
    parser.add_argument("ip", help="Destination IPv4 address to match")
    parser.add_argument("port", type=int, help="Destination port to match")
    parser.add_argument(
        "-i",
        "--input",
        default="custom_cca/context.txt",
        help="Path to the log file (default: custom_cca/context.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output image path (default: cwnd_<ip>_<port>.png)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the graph interactively in addition to saving it",
    )
    return parser.parse_args()


def extract_samples(log_path: Path, ip: str, port: int):
    timestamps = []
    cwnds = []

    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            match = LOG_PATTERN.match(line.strip())
            if not match:
                continue

            if match.group("ip") != ip or int(match.group("port")) != port:
                continue

            timestamps.append(float(match.group("timestamp")))
            cwnds.append(int(match.group("cwnd")))

    return timestamps, cwnds


def build_plot(timestamps, cwnds, ip: str, port: int, output_path: Path, show: bool):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "matplotlib is required to build the graph. Install it with: pip install matplotlib",
            file=sys.stderr,
        )
        return 1

    sample_counts = list(range(1, len(cwnds) + 1))

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, cwnds, marker="o", linewidth=1.5, markersize=4)
    plt.title(f"TCP cwnd for {ip}:{port}")
    plt.xlabel("time (seconds since first sample)")
    plt.ylabel("cwnd")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()

    return 0


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Input log file not found: {input_path}", file=sys.stderr)
        return 1

    output_name = args.output or f"cwnd_{args.ip.replace('.', '_')}_{args.port}.png"
    output_path = Path(output_name)

    timestamps, cwnds = extract_samples(input_path, args.ip, args.port)
    
    # make timestamps relative to the first sample for better plotting
    for time in range(1, len(timestamps)):
        timestamps[time] = timestamps[time] - timestamps[0]
    timestamps[0] = 0.0

    if not cwnds:
        print(
            f"No matching cwnd samples found for destination {args.ip}:{args.port} in {input_path}",
            file=sys.stderr,
        )
        return 1

    rc = build_plot(timestamps, cwnds, args.ip, args.port, output_path, args.show)
    if rc != 0:
        return rc

    print(
        f"Saved graph with {len(cwnds)} samples for {args.ip}:{args.port} to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
