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
import numpy as np

from result_parser import DEFAULT_CSV, REPORT_DIR, configs, read_csv, sorted_values


def main() -> int:
    rows = read_csv(DEFAULT_CSV)
    grouped = configs(rows)
    queues = sorted_values(rows, "queue_bytes")
    bursts = sorted_values(rows, "burst_bytes")
    rates = sorted_values(rows, "tgr_mbit")

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(14, 9),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )
    axes = axes.ravel()
    matrices = []

    for rate in rates:
        matrix = np.full((len(queues), len(bursts)), np.nan)
        for qi, queue in enumerate(queues):
            for bi, burst in enumerate(bursts):
                config = grouped.get((queue, burst, rate), {})
                if "empirical" not in config or "reno" not in config:
                    continue
                matrix[qi, bi] = (
                    config["empirical"].throughput_mib_s
                    - config["reno"].throughput_mib_s
                )
        matrices.append(matrix)

    finite_values = np.concatenate([matrix[np.isfinite(matrix)] for matrix in matrices])
    max_abs = max(abs(float(finite_values.min())), abs(float(finite_values.max())))

    for ax, rate, matrix in zip(axes, rates, matrices):
        image = ax.imshow(matrix, cmap="RdYlGn", vmin=-max_abs, vmax=max_abs, aspect="auto")
        ax.set_title(f"TGR {rate} Mbit/s")
        ax.set_xticks(range(len(bursts)))
        ax.set_xticklabels([str(burst) for burst in bursts], rotation=35)
        ax.set_yticks(range(len(queues)))
        ax.set_yticklabels([str(queue) for queue in queues])
        ax.set_xlabel("Burst bytes")
        ax.set_ylabel("Queue bytes")

        for qi in range(len(queues)):
            for bi in range(len(bursts)):
                value = matrix[qi, bi]
                if np.isfinite(value):
                    ax.text(
                        bi,
                        qi,
                        f"{value:+.1f}",
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="black",
                    )

    cbar = fig.colorbar(image, ax=axes.tolist(), shrink=0.88)
    cbar.set_label("Empirical - Reno throughput (MiB/s)")
    fig.suptitle("Empirical Throughput Gain Over TCP Reno", fontsize=15)

    output = REPORT_DIR / "images" / "empirical_gain_over_reno_heatmap.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
