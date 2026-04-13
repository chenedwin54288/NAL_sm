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

def build_plot(timestamps, cwnds):
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

    fig, ax = plt.subplots(figsize=(12, 5.5))

    ax.scatter(timestamps, cwnds, color='blue', s=28, zorder=3)

    if len(timestamps) > 1:
        ax.plot(timestamps, cwnds, color='blue', linewidth=1.8, alpha=0.9, zorder=2)

    ax.set_title("TCP cwnd vs Time (first N lines)")
    ax.set_xlabel("Time since first sample (ms)")
    ax.set_ylabel("cwnd")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig("temp_plot.png", dpi=150)
    plt.show()

    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Extract and plot cwnd from first N lines of log file.")
    parser.add_argument("log_file", help="Path to the log file")
    parser.add_argument("n_lines", type=int, help="Number of lines to process")
    args = parser.parse_args()

    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"Log file not found: {log_path}", file=sys.stderr)
        return 1

    timestamps, cwnds = extract_samples(log_path, args.n_lines)

    if not cwnds:
        print("No matching cwnd samples found in the first N lines", file=sys.stderr)
        return 1

    rc = build_plot(timestamps, cwnds)
    if rc != 0:
        return rc

    print(f"Saved plot with {len(cwnds)} samples to temp_plot.png")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())