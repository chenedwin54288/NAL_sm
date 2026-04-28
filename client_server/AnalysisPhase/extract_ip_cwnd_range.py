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

def extract_samples(log_path: Path, n_lines: int):
    timestamps = []
    cwnds = []

    with log_path.open("r", encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            if i >= n_lines:
                break
            match = LOG_PATTERN.match(line.strip())
            if not match:
                continue

            timestamps.append(float(match.group("timestamp")))
            cwnds.append(int(match.group("cwnd")))

    return timestamps, cwnds


def find_sharktooth_edges(timestamps, cwnds, drop_threshold):
    tops = []
    bottoms = []

    for i in range(1, len(cwnds)):
        prev_cwnd = cwnds[i - 1]
        curr_cwnd = cwnds[i]

        if prev_cwnd - curr_cwnd >= drop_threshold:
            tops.append((timestamps[i - 1], prev_cwnd))
            bottoms.append((timestamps[i], curr_cwnd))

    return tops, bottoms


def build_plot(timestamps, cwnds, top_points=None, bottom_points=None):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is required to build the graph. Install it with: pip install matplotlib", file=sys.stderr)
        return 1

    top_points = top_points or []
    bottom_points = bottom_points or []

    # Make timestamps relative to the first sample
    if timestamps:
        first_ts = timestamps[0]
        timestamps = [ts - first_ts for ts in timestamps]
        timestamps = [ts * 1000.0 for ts in timestamps]  # Convert to ms
        top_points = [((ts - first_ts) * 1000.0, cwnd) for ts, cwnd in top_points]
        bottom_points = [((ts - first_ts) * 1000.0, cwnd) for ts, cwnd in bottom_points]

    fig, ax = plt.subplots(figsize=(12, 5.5))

    ax.scatter(timestamps, cwnds, color='blue', s=28, zorder=3)

    if len(timestamps) > 1:
        ax.plot(timestamps, cwnds, color='blue', linewidth=1.8, alpha=0.9, zorder=2)

    if top_points:
        ax.scatter(
            [ts for ts, _ in top_points],
            [cwnd for _, cwnd in top_points],
            color='red',
            s=70,
            zorder=4,
            label='Sharktooth tops',
        )

    if bottom_points:
        ax.scatter(
            [ts for ts, _ in bottom_points],
            [cwnd for _, cwnd in bottom_points],
            color='green',
            s=70,
            zorder=4,
            label='Sharktooth bottoms',
        )

    ax.set_title("TCP cwnd vs Time (first N lines)")
    ax.set_xlabel("Time since first sample (ms)")
    ax.set_ylabel("cwnd")
    ax.grid(True, linestyle="--", alpha=0.4)
    if top_points or bottom_points:
        ax.legend()
    fig.tight_layout()
    fig.savefig("temp_plot.png", dpi=150)
    plt.show()

    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Extract and plot cwnd from first N lines of log file.")
    parser.add_argument("log_file", help="Path to the log file")
    parser.add_argument("n_lines", type=int, help="Number of lines to process")
    parser.add_argument(
        "--drop-threshold",
        type=int,
        default=10,
        help="Minimum cwnd drop between consecutive samples to count as a sharktooth edge",
    )
    args = parser.parse_args()

    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"Log file not found: {log_path}", file=sys.stderr)
        return 1

    timestamps, cwnds = extract_samples(log_path, args.n_lines)

    if not cwnds:
        print("No matching cwnd samples found in the first N lines", file=sys.stderr)
        return 1

    tops, bottoms = find_sharktooth_edges(timestamps, cwnds, args.drop_threshold)
    avg_tops_cwnd = sum(cwnd for _, cwnd in tops) / len(tops) if tops else 0
    avg_bottoms_cwnd = sum(cwnd for _, cwnd in bottoms) / len(bottoms) if bottoms else 0
    print(f"Found {len(tops)} sharktooth edges with drop threshold {args.drop_threshold}")
    print(f"Average top cwnd: {avg_tops_cwnd:.2f}, Average bottom cwnd: {avg_bottoms_cwnd:.2f}")
    print()

    if tops:
        for idx, ((top_ts, top_cwnd), (bottom_ts, bottom_cwnd)) in enumerate(zip(tops, bottoms), start=1):
            print(
                f"Edge {idx}: "
                f"top=({top_ts:.6f}s, {top_cwnd}), "
                f"bottom=({bottom_ts:.6f}s, {bottom_cwnd})"
            )
    else:
        print(f"No sharktooth edges found with drop threshold {args.drop_threshold}")

    rc = build_plot(timestamps, cwnds, tops, bottoms)
    if rc != 0:
        return rc

    print(f"Saved plot with {len(cwnds)} samples to temp_plot.png")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
