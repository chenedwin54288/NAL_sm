#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


REPORT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPORT_DIR / "all_results.md"
DEFAULT_CSV = REPORT_DIR / "generated" / "all_results.csv"

QUEUE_RE = re.compile(r"^## Queue Size = (?P<queue>\d+) bytes \(burst: (?P<burst>\d+)\)")
LOSS_RE = re.compile(r"^- Empirical max loss rate: (?P<loss>[0-9.]+)")
CELL_RE = re.compile(r"<\s*(?P<cwnd>[0-9.]+)\s*,\s*(?P<throughput>[0-9.]+)\s*>")

STRATEGY_COLUMNS = [
    ("TCP Reno (avg top cwnd)", "reno"),
    ("Empirical", "empirical"),
    ("BDP + Q_size - MSS", "bdp_plus_queue"),
    ("BDP", "bdp"),
]

DISPLAY_NAME = {
    "reno": "TCP Reno",
    "empirical": "Empirical",
    "bdp_plus_queue": "BDP + Q - MSS",
    "bdp": "BDP",
}

STRATEGY_ORDER = ["reno", "empirical", "bdp_plus_queue", "bdp"]


@dataclass(frozen=True)
class ResultRow:
    queue_bytes: int
    burst_bytes: int
    tgr_mbit: int
    strategy: str
    cwnd: float
    throughput_mib_s: float
    empirical_max_loss_rate: float | None


def parse_cell(cell: str) -> tuple[float, float]:
    match = CELL_RE.search(cell)
    if match is None:
        raise ValueError(f"Invalid result cell: {cell!r}")

    return float(match.group("cwnd")), float(match.group("throughput"))


def parse_results(path: Path = DEFAULT_INPUT) -> list[ResultRow]:
    rows: list[ResultRow] = []
    current_queue: int | None = None
    current_burst: int | None = None
    current_loss: float | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        loss_match = LOSS_RE.match(line)
        if loss_match:
            current_loss = float(loss_match.group("loss"))
            continue

        queue_match = QUEUE_RE.match(line)
        if queue_match:
            current_queue = int(queue_match.group("queue"))
            current_burst = int(queue_match.group("burst"))
            continue

        if not line.startswith("|") or "Mbit/s" not in line:
            continue
        if line.startswith("|---") or "TGR" in line:
            continue
        if current_queue is None or current_burst is None:
            raise ValueError(f"Found data row before queue heading: {line!r}")

        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) != 5:
            raise ValueError(f"Expected 5 columns, found {len(parts)} in {line!r}")

        tgr_mbit = int(parts[0].split()[0])
        for idx, (_, strategy) in enumerate(STRATEGY_COLUMNS, start=1):
            cwnd, throughput = parse_cell(parts[idx])
            rows.append(
                ResultRow(
                    queue_bytes=current_queue,
                    burst_bytes=current_burst,
                    tgr_mbit=tgr_mbit,
                    strategy=strategy,
                    cwnd=cwnd,
                    throughput_mib_s=throughput,
                    empirical_max_loss_rate=current_loss,
                )
            )

    return rows


def write_csv(rows: list[ResultRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "queue_bytes",
                "burst_bytes",
                "tgr_mbit",
                "strategy",
                "cwnd",
                "throughput_mib_s",
                "empirical_max_loss_rate",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def read_csv(path: Path = DEFAULT_CSV) -> list[ResultRow]:
    rows: list[ResultRow] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            loss = row.get("empirical_max_loss_rate")
            rows.append(
                ResultRow(
                    queue_bytes=int(row["queue_bytes"]),
                    burst_bytes=int(row["burst_bytes"]),
                    tgr_mbit=int(row["tgr_mbit"]),
                    strategy=row["strategy"],
                    cwnd=float(row["cwnd"]),
                    throughput_mib_s=float(row["throughput_mib_s"]),
                    empirical_max_loss_rate=float(loss) if loss else None,
                )
            )
    return rows


def configs(rows: list[ResultRow]) -> dict[tuple[int, int, int], dict[str, ResultRow]]:
    grouped: dict[tuple[int, int, int], dict[str, ResultRow]] = {}
    for row in rows:
        key = (row.queue_bytes, row.burst_bytes, row.tgr_mbit)
        grouped.setdefault(key, {})[row.strategy] = row
    return grouped


def sorted_values(rows: list[ResultRow], field: str) -> list[int]:
    return sorted({int(getattr(row, field)) for row in rows})


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def grouped_mean(
    rows: list[ResultRow],
    *,
    strategy: str,
    queue_bytes: int | None = None,
    burst_bytes: int | None = None,
    tgr_mbit: int | None = None,
    metric: str = "throughput_mib_s",
) -> float:
    values = [
        float(getattr(row, metric))
        for row in rows
        if row.strategy == strategy
        and (queue_bytes is None or row.queue_bytes == queue_bytes)
        and (burst_bytes is None or row.burst_bytes == burst_bytes)
        and (tgr_mbit is None or row.tgr_mbit == tgr_mbit)
    ]
    return mean(values)
