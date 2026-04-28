#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime

BACKLOG_PATTERN = re.compile(
    r"""
    ^(?P<timestamp>\d{2}:\d{2}:\d{2}\.\d+)  # 16:01:34.560783051
    \s+backlog\s+
    (?P<backlog>\d+)b                      # 0b or 585918b
    .*?requeues\s+
    (?P<requeues>\d+)                      # 213624
    """,
    re.VERBOSE,
)

def parse_timestamp(ts_str):
    # ts_str like "16:01:34.560783051"
    parts = ts_str.split('.')
    time_part = parts[0]  # "16:01:34"
    nano_part = parts[1]  # "560783051"
    dt = datetime.strptime(time_part, "%H:%M:%S")
    # Convert nanoseconds to seconds
    nano_seconds = int(nano_part) / 1e9
    total_seconds = dt.hour * 3600 + dt.minute * 60 + dt.second + nano_seconds
    return total_seconds

def extract_backlog(log_path: Path):
    timestamps = []
    backlogs = []
    requeues = []

    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            match = BACKLOG_PATTERN.match(line.strip())
            if not match:
                continue

            ts_str = match.group("timestamp")
            backlog = int(match.group("backlog"))
            requeue = int(match.group("requeues"))

            timestamps.append(parse_timestamp(ts_str))
            backlogs.append(backlog)
            requeues.append(requeue)

    # Compute requeues deltas
    deltas = []
    prev_requeue = None
    for rq in requeues:
        if prev_requeue is not None:
            deltas.append(rq - prev_requeue)
        else:
            deltas.append(0)  # First one has no delta
        prev_requeue = rq

    return timestamps, backlogs, deltas

def build_plot(timestamps, backlogs, deltas):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is required to build the graph. Install it with: pip install matplotlib", file=sys.stderr)
        return 1

    # Make timestamps relative to the first sample
    if timestamps:
        first_ts = timestamps[0]
        timestamps = [ts - first_ts for ts in timestamps]
        timestamps = [ts * 1000.0 for ts in timestamps]  # Convert to ms

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Backlog plot
    ax1.scatter(timestamps, backlogs, color='red', s=28, zorder=3)
    if len(timestamps) > 1:
        ax1.plot(timestamps, backlogs, color='red', linewidth=1.8, alpha=0.9, zorder=2)
    ax1.set_title("Network Backlog vs Time")
    ax1.set_xlabel("Time since first sample (ms)")
    ax1.set_ylabel("Backlog (bytes)")
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Requeues delta plot
    ax2.scatter(timestamps, deltas, color='blue', s=28, zorder=3)
    if len(timestamps) > 1:
        ax2.plot(timestamps, deltas, color='blue', linewidth=1.8, alpha=0.9, zorder=2)
    ax2.set_title("Requeues Delta vs Time")
    ax2.set_xlabel("Time since first sample (ms)")
    ax2.set_ylabel("Requeues Delta")
    ax2.grid(True, linestyle="--", alpha=0.4)

    fig.tight_layout()
    fig.savefig("backlog_and_deltas_plot.png", dpi=150)
    plt.show()

    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Extract and plot backlog from backlog.txt")
    parser.add_argument(
        "-i",
        "--input",
        default="backlog.txt",
        help="Path to the backlog log file (default: backlog.txt)",
    )
    args = parser.parse_args()

    log_path = Path(args.input)
    if not log_path.exists():
        print(f"Input log file not found: {log_path}", file=sys.stderr)
        return 1

    timestamps, backlogs, deltas = extract_backlog(log_path)

    if not backlogs:
        print("No backlog samples found", file=sys.stderr)
        return 1

    rc = build_plot(timestamps, backlogs, deltas)
    if rc != 0:
        return rc

    print(f"Saved plots with {len(backlogs)} samples to backlog_and_deltas_plot.png")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
