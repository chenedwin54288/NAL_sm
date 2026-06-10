#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from result_parser import DEFAULT_CSV, DISPLAY_NAME, REPORT_DIR, STRATEGY_ORDER, configs, mean, read_csv


def fmt(value: float) -> str:
    return f"{value:.2f}"


def main() -> int:
    rows = read_csv(DEFAULT_CSV)
    grouped = configs(rows)

    strategy_means = {
        strategy: mean(
            [row.throughput_mib_s for row in rows if row.strategy == strategy]
        )
        for strategy in STRATEGY_ORDER
    }

    win_counts = Counter()
    empirical_gains = []
    empirical_gains_by_queue: dict[int, list[float]] = defaultdict(list)
    empirical_gains_by_rate: dict[int, list[float]] = defaultdict(list)
    bdpq_gaps = []
    bdp_gaps = []

    for (queue, _burst, rate), strategy_rows in grouped.items():
        best = max(
            strategy_rows.values(),
            key=lambda row: (row.throughput_mib_s, -STRATEGY_ORDER.index(row.strategy)),
        )
        win_counts[best.strategy] += 1

        empirical = strategy_rows["empirical"].throughput_mib_s
        reno = strategy_rows["reno"].throughput_mib_s
        bdpq = strategy_rows["bdp_plus_queue"].throughput_mib_s
        bdp = strategy_rows["bdp"].throughput_mib_s

        gain = empirical - reno
        empirical_gains.append(gain)
        empirical_gains_by_queue[queue].append(gain)
        empirical_gains_by_rate[rate].append(gain)
        bdpq_gaps.append(empirical - bdpq)
        bdp_gaps.append(empirical - bdp)

    best_gain = max(
        (
            (
                strategy_rows["empirical"].throughput_mib_s
                - strategy_rows["reno"].throughput_mib_s,
                queue,
                burst,
                rate,
                strategy_rows["empirical"].throughput_mib_s,
                strategy_rows["reno"].throughput_mib_s,
            )
            for (queue, burst, rate), strategy_rows in grouped.items()
        ),
        key=lambda item: item[0],
    )

    worst_gain = min(
        (
            (
                strategy_rows["empirical"].throughput_mib_s
                - strategy_rows["reno"].throughput_mib_s,
                queue,
                burst,
                rate,
                strategy_rows["empirical"].throughput_mib_s,
                strategy_rows["reno"].throughput_mib_s,
            )
            for (queue, burst, rate), strategy_rows in grouped.items()
        ),
        key=lambda item: item[0],
    )

    queue_gain_lines = [
        f"| {queue} | {fmt(mean(values))} |"
        for queue, values in sorted(empirical_gains_by_queue.items())
    ]
    rate_gain_lines = [
        f"| {rate} | {fmt(mean(values))} |"
        for rate, values in sorted(empirical_gains_by_rate.items())
    ]

    lines = [
        "# Report 4 Analysis",
        "",
        "This README is generated from `generated/all_results.csv` by `scripts/write_analysis_readme.py`.",
        "",
        "## Generated Diagrams",
        "",
        "- ![Mean throughput by strategy and queue size](images/strategy_throughput_by_queue.png)",
        "- ![Empirical burst sensitivity](images/empirical_burst_sensitivity.png)",
        "- ![Empirical gain over Reno heatmap](images/empirical_gain_over_reno_heatmap.png)",
        "- ![CWND selection by queue](images/cwnd_selection_by_queue.png)",
        "- ![Best strategy counts](images/best_strategy_counts.png)",
        "",
        "## Summary Metrics",
        "",
        f"- Parsed configurations: {len(grouped)} queue/burst/rate points.",
        f"- Parsed strategy rows: {len(rows)}.",
        f"- Mean throughput over all points: TCP Reno {fmt(strategy_means['reno'])} MiB/s, "
        f"Empirical {fmt(strategy_means['empirical'])} MiB/s, "
        f"BDP + Q - MSS {fmt(strategy_means['bdp_plus_queue'])} MiB/s, "
        f"BDP + 1 MSS {fmt(strategy_means['bdp'])} MiB/s.",
        f"- Mean Empirical minus Reno throughput: {fmt(mean(empirical_gains))} MiB/s.",
        f"- Mean Empirical minus BDP + Q - MSS throughput: {fmt(mean(bdpq_gaps))} MiB/s.",
        f"- Mean Empirical minus BDP + 1 MSS throughput: {fmt(mean(bdp_gaps))} MiB/s.",
        "",
        "Best-throughput winner counts:",
        "",
        "| Strategy | Wins |",
        "|---|---:|",
    ]

    for strategy in STRATEGY_ORDER:
        lines.append(f"| {DISPLAY_NAME[strategy]} | {win_counts[strategy]} |")

    lines.extend(
        [
            "",
            "Average Empirical minus Reno gain by queue:",
            "",
            "| Queue bytes | Mean gain (MiB/s) |",
            "|---:|---:|",
            *queue_gain_lines,
            "",
            "Average Empirical minus Reno gain by TGR:",
            "",
            "| TGR (Mbit/s) | Mean gain (MiB/s) |",
            "|---:|---:|",
            *rate_gain_lines,
            "",
            "Largest positive Empirical-over-Reno case:",
            "",
            f"- Queue {best_gain[1]} B, burst {best_gain[2]} B, TGR {best_gain[3]} Mbit/s: "
            f"Empirical {fmt(best_gain[4])} MiB/s vs Reno {fmt(best_gain[5])} MiB/s "
            f"({best_gain[0]:+.2f} MiB/s).",
            "",
            "Largest negative Empirical-over-Reno case:",
            "",
            f"- Queue {worst_gain[1]} B, burst {worst_gain[2]} B, TGR {worst_gain[3]} Mbit/s: "
            f"Empirical {fmt(worst_gain[4])} MiB/s vs Reno {fmt(worst_gain[5])} MiB/s "
            f"({worst_gain[0]:+.2f} MiB/s).",
            "",
            "## Observations",
            "",
            "1. Empirical CWND is the most reliable high-throughput choice in the small-queue cases. "
            "For 6250 B and 12500 B queues, Reno and the fixed BDP formulas often collapse at higher TGRs, "
            "while the empirical cap keeps throughput close to the bottleneck rate.",
            "",
            "2. The simple `BDP + Q_size - MSS` CWND is too aggressive when the queue is small. "
            "It asks for CWND values like 37 at 1 Gbit/s with a 6250 B queue, but throughput stays around "
            "12-16 MiB/s in many burst settings. This matches the earlier suspicion that configured queue size "
            "is not fully usable when enqueue bursts consume the TBF queue.",
            "",
            "3. As queue size grows, the formulas become much less dangerous. At 50000 B and 100000 B queues, "
            "all strategies are often close to line rate, and `BDP + Q_size - MSS` sometimes wins outright.",
            "",
            "4. Burst size matters most for small queues and high TGR. With a 6250 B queue, empirical throughput "
            "at 750-1000 Mbit/s improves sharply when moving away from the smallest burst setting, but Reno and "
            "the fixed formulas remain unstable. For larger queues, burst sensitivity is much flatter.",
            "",
            "5. The empirical CWND generally tracks the Reno average-top CWND, but floors it or steps downward "
            "to satisfy the loss threshold. This is visible in the CWND plot: empirical values stay below Reno "
            "tops, while `BDP + Q_size - MSS` can be far above both for large queues.",
            "",
            "6. The data mixes empirical-loss thresholds: the 6250 B and 12500 B sections use 0.20, while later "
            "sections use 0.05. Comparisons of empirical choices across those queue ranges should be interpreted "
            "with that threshold change in mind.",
            "",
            "## Regeneration",
            "",
            "Run all scripts from `client_server/report4`:",
            "",
            "```bash",
            "./scripts/generate_all.sh",
            "```",
            "",
        ]
    )

    output = REPORT_DIR / "README.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
