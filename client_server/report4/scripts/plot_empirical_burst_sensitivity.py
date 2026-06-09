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

from result_parser import DEFAULT_CSV, REPORT_DIR, grouped_mean, read_csv, sorted_values


def main() -> int:
    rows = read_csv(DEFAULT_CSV)
    queues = sorted_values(rows, "queue_bytes")
    bursts = sorted_values(rows, "burst_bytes")
    rates = sorted_values(rows, "tgr_mbit")

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True, sharey=False)
    axes = axes.ravel()

    for ax, rate in zip(axes, rates):
        for queue in queues:
            values = [
                grouped_mean(
                    rows,
                    strategy="empirical",
                    queue_bytes=queue,
                    burst_bytes=burst,
                    tgr_mbit=rate,
                    metric="throughput_mib_s",
                )
                for burst in bursts
            ]
            ax.plot(bursts, values, marker="o", linewidth=2, label=f"Q={queue} B")

        ax.set_title(f"TGR {rate} Mbit/s")
        ax.set_xscale("log")
        ax.set_xticks(bursts)
        ax.set_xticklabels([str(burst) for burst in bursts], rotation=30)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("TBF burst (bytes, log scale)")
        ax.set_ylabel("Empirical throughput (MiB/s)")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=len(queues), frameon=False)
    fig.suptitle("Empirical Throughput Sensitivity to TBF Burst Size", fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.90))

    output = REPORT_DIR / "images" / "empirical_burst_sensitivity.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
