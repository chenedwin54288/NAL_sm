#!/usr/bin/env python3

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"),
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from result_parser import DEFAULT_CSV, DISPLAY_NAME, REPORT_DIR, STRATEGY_ORDER, configs, read_csv


def main() -> int:
    rows = read_csv(DEFAULT_CSV)
    grouped = configs(rows)
    winners = Counter()

    for strategy_rows in grouped.values():
        if not strategy_rows:
            continue
        best = max(
            strategy_rows.values(),
            key=lambda row: (row.throughput_mib_s, -STRATEGY_ORDER.index(row.strategy)),
        )
        winners[best.strategy] += 1

    labels = [DISPLAY_NAME[strategy] for strategy in STRATEGY_ORDER]
    values = [winners[strategy] for strategy in STRATEGY_ORDER]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, values, color=["#5B8FF9", "#61DDAA", "#65789B", "#F6BD16"])
    ax.set_ylabel("Number of configurations won")
    ax.set_title("Best-Throughput Strategy Counts")
    ax.grid(True, axis="y", alpha=0.3)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            str(value),
            ha="center",
            va="bottom",
        )

    fig.tight_layout()
    output = REPORT_DIR / "images" / "best_strategy_counts.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
