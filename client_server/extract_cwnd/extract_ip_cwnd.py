#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path

LOG_PATTERN = re.compile(
    r"""
    ^\[\s*(?P<timestamp>\d+\.\d+)\]      # [ 4215.320700]
    .*?cwnd=(?P<cwnd>\d+)                # cwnd=3069
    .*?Destination:\s+
    (?P<ip>[\d.]+)                       # 128.178.122.39
    :(?P<port>\d+)                       # 38880
    """,
    re.VERBOSE,
)

CA_STATE_PATTERN = re.compile(r"\bca_state=(?P<ca_state>[a-zA-Z_]+)(?:\(\d+\))?\b")
CA_PHASE_PATTERN = re.compile(r"\bphase=(?P<phase>[a-zA-Z_]+)(?:\(\d+\))?\b")

CA_STATE_COLORS = {
    "open": "green",
    "disorder": "orange",
    "cwr": "purple",
    "recovery": "red",
    "loss": "brown",
    "unknown": "gray",
}

CA_PHASE_COLORS = {
    "slow_start": "green",
    "fast_retransmit": "orange",
    "loss_recovery": "red",
    "congestion_avoidance": "gray",
}


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
    parser.add_argument(
        "-gb",
        "--gb",
        default="others",
        help="save the graph in a subfolder named after the GB (default: others)",
    )
    return parser.parse_args()


def extract_samples(log_path: Path, gb: int, ip: str, port: int):
    timestamps = []
    cwnds = []
    ca_phases = []

    with log_path.open("r", encoding="utf-8") as handle, open(f"outputs/{gb} GB/{port}/cwnd_{ip.replace('.', '_')}_{port}_log.txt", "w") as log:
        for line in handle:
            match = LOG_PATTERN.match(line.strip())
            if not match:
                continue

            if match.group("ip") != ip or int(match.group("port")) != port:
                continue

            log.writelines(line)     

            timestamps.append(float(match.group("timestamp")))

            cwnds.append(int(match.group("cwnd")))

            # ca_state_match = CA_STATE_PATTERN.search(line)
            ca_phase_match = CA_PHASE_PATTERN.search(line)
            ca_phases.append(
                ca_phase_match.group("phase").lower() if ca_phase_match else "unknown"
            )

    return timestamps, cwnds, ca_phases


def build_plot(timestamps, cwnds, ca_phases, ip: str, port: int, output_path: Path, show: bool):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
    except ImportError:
        print(
            "matplotlib is required to build the graph. Install it with: pip install matplotlib",
            file=sys.stderr,
        )
        return 1

    seen_states = []

    timestamps = [ts * 1000.0 for ts in timestamps]
    time_unit = "ms"

    fig, ax = plt.subplots(figsize=(12, 5.5))

    for idx, ca_phase in enumerate(ca_phases):
        color = CA_PHASE_COLORS[ca_phase]
        if ca_phase not in seen_states:
            seen_states.append(ca_phase)

        ax.scatter(
            timestamps[idx],
            cwnds[idx],
            color=color,
            s=28,
            zorder=3,
        )

        if idx > 0:
            ax.plot(
                timestamps[idx - 1:idx + 1],
                cwnds[idx - 1:idx + 1],
                color=color,
                linewidth=1.8,
                alpha=0.9,
                zorder=2,
            )

    legend_handles = [
        Line2D(
            [0],
            [0],
            color=CA_PHASE_COLORS[ca_phase],
            lw=2,
            marker="o",
            label=ca_phase,
        )
        for ca_phase in seen_states
    ]

    ax.set_title(f"TCP cwnd for {ip}:{port}")
    ax.set_xlabel(f"Time since first sample ({time_unit})")
    ax.set_ylabel("cwnd")
    ax.grid(True, linestyle="--", alpha=0.4)
    if legend_handles:
        ax.legend(handles=legend_handles, title="CA State")
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

    output_name = args.output or f"outputs/{args.gb} GB/{args.port}/cwnd_{args.ip.replace('.', '_')}_{args.port}.png"
    output_path = Path(output_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    timestamps, cwnds, ca_phases = extract_samples(input_path, args.gb, args.ip, args.port)
    
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

    rc = build_plot(timestamps, cwnds, ca_phases, args.ip, args.port, output_path, args.show)
    if rc != 0:
        return rc

    print(
        f"Saved graph with {len(cwnds)} samples for {args.ip}:{args.port} to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
