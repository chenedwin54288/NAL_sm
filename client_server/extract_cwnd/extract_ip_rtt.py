#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

LOG_PATTERN = re.compile(
    r"""
    ^\[\s*(?P<timestamp>\d+\.\d+)\]      # [181680.769277]
    .*?rtt=(?P<rtt>\d+)                  # rtt=138
    .*?phase=(?P<phase>[a-zA-Z_]+)       # phase=slow_start
    .*?Destination:\s+
    (?P<ip>[\d.]+)                       # 128.178.122.39
    :(?P<port>\d+)                       # 56370
    """,
    re.VERBOSE,
)

PHASE_COLORS = {
    "slow_start": "green",
    "fast_retransmit": "orange",
    "loss_recovery": "red",
    "congestion_avoidance": "gray",
    "unknown": "blue",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract RTT samples for a destination IP:port and plot them."
    )
    parser.add_argument("ip", help="Destination IPv4 address to match")
    parser.add_argument("port", type=int, help="Destination port to match")
    parser.add_argument(
        "-i",
        "--input",
        default=str(BASE_DIR / "context.txt"),
        help="Path to the log file (default: context.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output image path (default: rtt_<ip>_<port>.png)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the graph interactively in addition to saving it",
    )
    parser.add_argument(
        "-gb",
        "--gb",
        default="others",
        help="Save the graph in a subfolder named after the GB value (default: others)",
    )
    return parser.parse_args()


def extract_samples(log_path: Path, gb: str, ip: str, port: int):
    timestamps = []
    rtts = []
    phases = []

    log_output = BASE_DIR / f"outputs/{gb} GB/{port}/rtt_{ip.replace('.', '_')}_{port}_log.txt"
    log_output.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("r", encoding="utf-8") as handle, log_output.open(
        "w", encoding="utf-8"
    ) as log:
        for line in handle:
            match = LOG_PATTERN.match(line.strip())
            if not match:
                continue

            if match.group("ip") != ip or int(match.group("port")) != port:
                continue

            log.write(line)
            timestamps.append(float(match.group("timestamp")))
            rtts.append(int(match.group("rtt")))
            phases.append(match.group("phase").lower())

    return timestamps, rtts, phases


def build_plot(timestamps, rtts, phases, ip: str, port: int, output_path: Path, show: bool):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
    except ImportError:
        print(
            "matplotlib is required to build the graph. Install it with: pip install matplotlib",
            file=sys.stderr,
        )
        return 1

    seen_phases = []
    fig, ax = plt.subplots(figsize=(11, 5.5))

    for idx, phase in enumerate(phases):
        color = PHASE_COLORS.get(phase, PHASE_COLORS["unknown"])
        if phase not in seen_phases:
            seen_phases.append(phase)

        ax.scatter(
            timestamps[idx],
            rtts[idx],
            color=color,
            s=28,
            zorder=3,
        )

        if idx > 0:
            ax.plot(
                timestamps[idx - 1 : idx + 1],
                rtts[idx - 1 : idx + 1],
                color=PHASE_COLORS.get(phase, PHASE_COLORS["unknown"]),
                linewidth=1.8,
                alpha=0.9,
                zorder=2,
            )

    legend_handles = [
        Line2D(
            [0],
            [0],
            color=PHASE_COLORS.get(phase, PHASE_COLORS["unknown"]),
            lw=2,
            marker="o",
            label=phase,
        )
        for phase in seen_phases
    ]

    ax.set_title(f"TCP RTT for {ip}:{port}")
    ax.set_xlabel("Time since first sample (s)")
    ax.set_ylabel("RTT (us)")
    ax.grid(True, linestyle="--", alpha=0.4)
    if legend_handles:
        ax.legend(handles=legend_handles, title="Phase")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close(fig)

    return 0


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Input log file not found: {input_path}", file=sys.stderr)
        return 1

    output_name = args.output or (
        f"outputs/{args.gb} GB/{args.port}/rtt_{args.ip.replace('.', '_')}_{args.port}.png"
    )
    output_path = Path(output_name)
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamps, rtts, phases = extract_samples(input_path, args.gb, args.ip, args.port)

    if not rtts:
        print(
            f"No matching RTT samples found for destination {args.ip}:{args.port} in {input_path}",
            file=sys.stderr,
        )
        return 1

    first_timestamp = timestamps[0]
    timestamps = [timestamp - first_timestamp for timestamp in timestamps]

    rc = build_plot(timestamps, rtts, phases, args.ip, args.port, output_path, args.show)
    if rc != 0:
        return rc

    print(
        f"Saved graph with {len(rtts)} RTT samples for {args.ip}:{args.port} to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
