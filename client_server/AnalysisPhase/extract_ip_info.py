#!/usr/bin/env python3

# Example command:
#   python3 AnalysisPhase/extract_ip_info.py \
#     -i AnalysisPhase/filtered_56988.csv \
#     -o AnalysisPhase/filtered_56988_summary.json

import argparse
import csv
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "filtered_context.csv"
DEFAULT_OUTPUT = SCRIPT_DIR / "ip_info.json"
REQUIRED_COLUMNS = {"timestamp", "rtt", "phase"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract summary information from a filtered cwnd CSV file."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=str(DEFAULT_INPUT),
        help=f"Path to filtered CSV file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Path to output JSON file (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def validate_columns(fieldnames) -> None:
    missing_columns = REQUIRED_COLUMNS - set(fieldnames or [])
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV file is missing required columns: {missing}")


def extract_ip_info(csv_path: Path) -> dict:
    phase_counts = {}
    rtt_total = 0
    rtt_count = 0
    row_count = 0
    first_timestamp = None
    last_timestamp = None
    min_timestamp = None
    max_timestamp = None

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        validate_columns(reader.fieldnames)

        for row in reader:
            row_count += 1

            phase = row["phase"] or "unknown"
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

            rtt = row["rtt"]
            if rtt:
                rtt_total += int(rtt)
                rtt_count += 1

            timestamp = row["timestamp"]
            if timestamp:
                timestamp_value = float(timestamp)
                if first_timestamp is None:
                    first_timestamp = timestamp_value
                last_timestamp = timestamp_value
                if min_timestamp is None or timestamp_value < min_timestamp:
                    min_timestamp = timestamp_value
                if max_timestamp is None or timestamp_value > max_timestamp:
                    max_timestamp = timestamp_value

    average_rtt = None
    if rtt_count > 0:
        average_rtt = rtt_total / rtt_count

    transfer_time_seconds = None
    if min_timestamp is not None and max_timestamp is not None:
        transfer_time_seconds = max_timestamp - min_timestamp

    return {
        "csv_file": str(csv_path),
        "row_count": row_count,
        "phase_counts": phase_counts,
        "average_rtt": average_rtt,
        "average_rtt_sample_count": rtt_count,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "min_timestamp": min_timestamp,
        "max_timestamp": max_timestamp,
        "transfer_time_seconds": transfer_time_seconds,
    }


def write_json(output_path: Path, info: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(info, output_file, indent=2)
        output_file.write("\n")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input CSV file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        info = extract_ip_info(input_path)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    write_json(output_path, info)
    print(f"Wrote JSON summary for {info['row_count']} CSV rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
