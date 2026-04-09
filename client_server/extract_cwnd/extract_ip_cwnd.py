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

CA_STATE_COLORS = {
    "open": "green",
    "disorder": "orange",
    "cwr": "purple",
    "recovery": "red",
    "loss": "brown",
    "unknown": "gray",
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
    return parser.parse_args()


def extract_samples(log_path: Path, ip: str, port: int):
    timestamps = []
    cwnds = []
    ca_states = []

    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            match = LOG_PATTERN.match(line.strip())
            if not match:
                continue

            if match.group("ip") != ip or int(match.group("port")) != port:
                continue

            timestamps.append(float(match.group("timestamp")))
            cwnds.append(int(match.group("cwnd")))
            ca_state_match = CA_STATE_PATTERN.search(line)
            #print(ca_state_match)
            ca_states.append(
                ca_state_match.group("ca_state").lower() if ca_state_match else "unknown"
            )

    return timestamps, cwnds, ca_states


def build_plot(timestamps, cwnds, ca_states, ip: str, port: int, output_path: Path, show: bool):
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

    fig, ax = plt.subplots(figsize=(11, 5.5))

    for idx, ca_state in enumerate(ca_states):
        color = CA_STATE_COLORS.get(ca_state, CA_STATE_COLORS["unknown"])
        if ca_state not in seen_states:
            seen_states.append(ca_state)

        ax.scatter(
            timestamps[idx],
            cwnds[idx],
            color=color,
            s=28,
            zorder=3,
        )

        if idx > 0:
            prev_ca_state = ca_states[idx - 1]
            line_color = CA_STATE_COLORS.get(prev_ca_state, CA_STATE_COLORS["unknown"])
            ax.plot(
                timestamps[idx - 1:idx + 1],
                cwnds[idx - 1:idx + 1],
                color=line_color,
                linewidth=1.8,
                alpha=0.9,
                zorder=2,
            )

    legend_handles = [
        Line2D(
            [0],
            [0],
            color=CA_STATE_COLORS.get(ca_state, CA_STATE_COLORS["unknown"]),
            lw=2,
            marker="o",
            label=ca_state,
        )
        for ca_state in seen_states
    ]

    ax.set_title(f"TCP cwnd for {ip}:{port}")
    ax.set_xlabel("Time since first sample (s)")
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

    output_name = args.output or f"outputs/cwnd_{args.ip.replace('.', '_')}_{args.port}.png"
    output_path = Path(output_name)

    timestamps, cwnds, ca_states = extract_samples(input_path, args.ip, args.port)
    
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

    rc = build_plot(timestamps, cwnds, ca_states, args.ip, args.port, output_path, args.show)
    if rc != 0:
        return rc

    print(
        f"Saved graph with {len(cwnds)} samples for {args.ip}:{args.port} to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
