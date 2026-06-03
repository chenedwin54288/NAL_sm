#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


DEFAULT_MSS_BYTES = 1460
DEFAULT_RTT_MS = 0.4

BYTE_UNITS = {
    "": 1.0,
    "b": 1.0,
    "byte": 1.0,
    "bytes": 1.0,
    "k": 1_000.0,
    "kb": 1_000.0,
    "kbyte": 1_000.0,
    "kbytes": 1_000.0,
    "kib": 1024.0,
    "m": 1_000_000.0,
    "mb": 1_000_000.0,
    "mbyte": 1_000_000.0,
    "mbytes": 1_000_000.0,
    "mib": 1024.0**2,
}


def parse_bytes(value: str) -> int:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid byte value: {value!r}")

    number = float(match.group(1))
    unit = (match.group(2) or "").lower()
    if unit not in BYTE_UNITS:
        supported = ", ".join(sorted(unit for unit in BYTE_UNITS if unit))
        raise argparse.ArgumentTypeError(
            f"Unsupported byte unit {unit!r}; supported units: {supported}"
        )

    return int(number * BYTE_UNITS[unit])


def extract_json_from_line(line: str) -> dict[str, Any] | None:
    if (
        "FinalResults:" not in line
        and "SERVER RESPONSE" not in line
        and "xput_avg_original" not in line
    ):
        return None

    start = line.find("{")
    end = line.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        payload = json.loads(line[start : end + 1])
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def load_result_records(results_dir: Path, since_epoch: float | None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in results_dir.rglob("*.txt"):
        try:
            stat = path.stat()
        except OSError:
            continue

        if since_epoch is not None and stat.st_mtime < since_epoch:
            continue

        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for line_number, line in enumerate(lines, start=1):
            payload = extract_json_from_line(line)
            if payload is None:
                continue

            records.append(
                {
                    "mtime": stat.st_mtime,
                    "line_number": line_number,
                    "source_file": str(path),
                    "result": payload,
                }
            )

    records.sort(
        key=lambda record: (record["mtime"], record["line_number"]),
        reverse=True,
    )
    return records


def parse_throughput(value: Any, field_name: str) -> float:
    try:
        throughput = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} is not numeric: {value!r}") from exc

    if throughput <= 0:
        raise ValueError(f"{field_name} must be greater than zero: {throughput}")

    return throughput


def calculate_rwnd(
    throughput_mbit_per_second: float,
    rtt_ms: float,
    mss_bytes: int,
    queue_bytes: int | None,
) -> dict[str, Any]:
    bdp_bytes = throughput_mbit_per_second * 1_000_000.0 * (rtt_ms / 1000.0) / 8.0

    if queue_bytes is None:
        formula = "ceil(BDP / MSS)"
        rwnd_segments_raw = math.ceil(bdp_bytes / mss_bytes)
        byte_budget = bdp_bytes
    else:
        formula = "floor(max(BDP + queue - MSS, MSS) / MSS)"
        byte_budget = max(bdp_bytes + queue_bytes - mss_bytes, float(mss_bytes))
        rwnd_segments_raw = math.floor(byte_budget / mss_bytes)

    rwnd_segments = max(1, int(rwnd_segments_raw))
    return {
        "throughput_mbit_per_second": throughput_mbit_per_second,
        "rtt_ms": rtt_ms,
        "mss_bytes": mss_bytes,
        "queue_bytes": queue_bytes,
        "bdp_bytes": bdp_bytes,
        "byte_budget": byte_budget,
        "formula": formula,
        "rwnd_segments": rwnd_segments,
        "rwnd_bytes": rwnd_segments * mss_bytes,
    }


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    source_file = None
    result_payload: dict[str, Any] | None = None

    if args.throughput_mbit is None:
        records = load_result_records(args.results_dir, args.since_epoch)
        if not records:
            since_note = (
                f" modified after {args.since_epoch}"
                if args.since_epoch is not None
                else ""
            )
            raise SystemExit(
                f"No WeHe result JSON found under {args.results_dir}{since_note}"
            )

        selected = records[0]
        source_file = selected["source_file"]
        result_payload = selected["result"]
        if args.throughput_field not in result_payload:
            fields = ", ".join(sorted(result_payload))
            raise SystemExit(
                f"{args.throughput_field!r} not found in {source_file}. "
                f"Available fields: {fields}"
            )
        throughput = parse_throughput(
            result_payload[args.throughput_field],
            args.throughput_field,
        )
    else:
        throughput = parse_throughput(args.throughput_mbit, "--throughput-mbit")

    result = calculate_rwnd(
        throughput_mbit_per_second=throughput,
        rtt_ms=args.rtt_ms,
        mss_bytes=args.mss_bytes,
        queue_bytes=args.queue_bytes,
    )
    result.update(
        {
            "source_file": source_file,
            "throughput_field": args.throughput_field,
        }
    )
    if result_payload is not None:
        result["wehe_result"] = result_payload

    return result


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    default_results_dir = script_dir / "client" / "wehe-cmdline" / "results"

    parser = argparse.ArgumentParser(
        description="Extract WeHe throughput and calculate a client rwnd segment count."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=default_results_dir,
        help=f"WeHe result directory (default: {default_results_dir})",
    )
    parser.add_argument(
        "--since-epoch",
        type=float,
        default=None,
        help="Only consider result files modified at or after this Unix epoch time.",
    )
    parser.add_argument(
        "--throughput-field",
        default="xput_avg_original",
        help="WeHe JSON field to use as Mbit/s throughput (default: xput_avg_original).",
    )
    parser.add_argument(
        "--throughput-mbit",
        type=float,
        default=None,
        help="Use this Mbit/s throughput directly instead of reading WeHe result logs.",
    )
    parser.add_argument(
        "--rtt-ms",
        type=float,
        default=DEFAULT_RTT_MS,
        help=f"RTT in milliseconds for the BDP calculation (default: {DEFAULT_RTT_MS}).",
    )
    parser.add_argument(
        "--mss-bytes",
        type=int,
        default=DEFAULT_MSS_BYTES,
        help=f"MSS bytes used for rwnd segments (default: {DEFAULT_MSS_BYTES}).",
    )
    parser.add_argument(
        "--queue-bytes",
        "--tbf-limit",
        dest="queue_bytes",
        type=parse_bytes,
        default=None,
        help="Optional queue/TBF limit, for example 50000b. Enables BDP + queue - MSS mode.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete calculation as JSON.",
    )
    parser.add_argument(
        "--value-only",
        action="store_true",
        help="Print only the rwnd segment count.",
    )
    args = parser.parse_args()

    if args.rtt_ms <= 0:
        parser.error("--rtt-ms must be greater than zero")
    if args.mss_bytes <= 0:
        parser.error("--mss-bytes must be greater than zero")
    if args.queue_bytes is not None and args.queue_bytes < 0:
        parser.error("--queue-bytes/--tbf-limit must be non-negative")

    return args


def print_human_readable(result: dict[str, Any]) -> None:
    source_file = result.get("source_file") or "manual --throughput-mbit"
    print(f"Source: {source_file}")
    print(
        "Throughput: "
        f"{result['throughput_mbit_per_second']:.6f} Mbit/s "
        f"({result['throughput_field']})"
    )
    print(f"RTT: {result['rtt_ms']:.6g} ms")
    print(f"MSS: {result['mss_bytes']} bytes")
    if result["queue_bytes"] is not None:
        print(f"Queue: {result['queue_bytes']} bytes")
    print(f"Formula: {result['formula']}")
    print(f"BDP: {result['bdp_bytes']:.2f} bytes")
    print(f"rwnd_segments: {result['rwnd_segments']}")
    print(f"rwnd_bytes: {result['rwnd_bytes']}")


def main() -> int:
    args = parse_args()
    result = build_result(args)

    if args.value_only:
        print(result["rwnd_segments"])
    elif args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human_readable(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
