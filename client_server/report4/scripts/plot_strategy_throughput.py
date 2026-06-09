#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"),
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from result_parser import (
    DEFAULT_CSV,
    DISPLAY_NAME,
    REPORT_DIR,
    STRATEGY_ORDER,
    grouped_mean,
    read_csv,
    sorted_values,
)


def main() -> int:
    rows = read_csv(DEFAULT_CSV)
    queues = sorted_values(rows, "queue_bytes")
    rates = sorted_values(rows, "tgr_mbit")

    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
    axes = axes.ravel()

    for ax, queue in zip(axes, queues):
        for strategy in STRATEGY_ORDER:
            values = [
                grouped_mean(
                    rows,
                    strategy=strategy,
                    queue_bytes=queue,
                    tgr_mbit=rate,
                    metric="throughput_mib_s",
                )
                for rate in rates
            ]
            ax.plot(rates, values, marker="o", linewidth=2, label=DISPLAY_NAME[strategy])

        ax.set_title(f"Queue {queue} B")
        ax.grid(True, alpha=0.3)
        ax.set_xticks(rates)
        ax.set_xlabel("TGR (Mbit/s)")
        ax.set_ylabel("Mean throughput (MiB/s)")

    axes[-1].axis("off")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[-1].legend(handles, labels, loc="center", frameon=False)

    fig.suptitle("Mean Throughput by Strategy and Queue Size", fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    output = REPORT_DIR / "images" / "strategy_throughput_by_queue.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
