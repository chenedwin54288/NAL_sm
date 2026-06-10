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
THROUGHPUT_BYTE_SOURCE = "bytes_acked"


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
    parser.add_argument(
        "--cwnd-limit",
        type=int,
        default=0,
        help=(
            "Configured cwnd cap in MSS-sized segments. If slow-start exit is not "
            "detected, throughput starts at the first sample where cwnd reaches this cap."
        ),
    )
    return parser.parse_args()


def validate_columns(fieldnames) -> None:
    missing_columns = REQUIRED_COLUMNS - set(fieldnames or [])
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV file is missing required columns: {missing}")


def parse_float(value):
    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value):
    if not value:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def new_byte_sample(row):
    timestamp = parse_float(row.get("timestamp"))
    byte_count = parse_int(row.get(THROUGHPUT_BYTE_SOURCE))

    if timestamp is None or byte_count is None:
        return None

    return {
        "timestamp": timestamp,
        "bytes": byte_count,
        "phase": (row.get("phase") or "unknown").lower(),
        "seq": row.get("seq") or "",
        "cwnd": parse_int(row.get("cwnd")),
        "bytes_acked": parse_int(row.get("bytes_acked")),
        "bytes_sent": parse_int(row.get("bytes_sent")),
    }


def summarize_post_slow_start(
    slow_start_end_sample,
    final_sample,
    cwnd_cap_reached_sample=None,
    cwnd_limit=0,
):
    summary = {
        "throughput_start_reason": None,
        "post_slow_start_byte_source": THROUGHPUT_BYTE_SOURCE,
        "slow_start_end_timestamp": None,
        "slow_start_end_phase": None,
        "slow_start_end_seq": None,
        "slow_start_end_cwnd": None,
        "slow_start_end_bytes_acked": None,
        "slow_start_end_bytes_sent": None,
        "cwnd_limit": cwnd_limit if cwnd_limit > 0 else None,
        "cwnd_cap_reached_timestamp": None,
        "cwnd_cap_reached_phase": None,
        "cwnd_cap_reached_seq": None,
        "cwnd_cap_reached_cwnd": None,
        "cwnd_cap_reached_bytes_acked": None,
        "cwnd_cap_reached_bytes_sent": None,
        "final_timestamp": None,
        "final_bytes_acked": None,
        "final_bytes_sent": None,
        "post_slow_start_elapsed_seconds": None,
        "post_slow_start_bytes": None,
        "post_slow_start_mbit_per_second": None,
        "post_slow_start_mib_per_second": None,
    }

    if final_sample is None:
        return summary

    summary.update(
        {
            "final_timestamp": final_sample["timestamp"],
            "final_bytes_acked": final_sample["bytes_acked"],
            "final_bytes_sent": final_sample["bytes_sent"],
        }
    )

    if slow_start_end_sample is not None:
        summary.update(
            {
                "slow_start_end_timestamp": slow_start_end_sample["timestamp"],
                "slow_start_end_phase": slow_start_end_sample["phase"],
                "slow_start_end_seq": slow_start_end_sample["seq"],
                "slow_start_end_cwnd": slow_start_end_sample["cwnd"],
                "slow_start_end_bytes_acked": slow_start_end_sample["bytes_acked"],
                "slow_start_end_bytes_sent": slow_start_end_sample["bytes_sent"],
            }
        )

    if cwnd_cap_reached_sample is not None:
        summary.update(
            {
                "cwnd_cap_reached_timestamp": cwnd_cap_reached_sample["timestamp"],
                "cwnd_cap_reached_phase": cwnd_cap_reached_sample["phase"],
                "cwnd_cap_reached_seq": cwnd_cap_reached_sample["seq"],
                "cwnd_cap_reached_cwnd": cwnd_cap_reached_sample["cwnd"],
                "cwnd_cap_reached_bytes_acked": cwnd_cap_reached_sample["bytes_acked"],
                "cwnd_cap_reached_bytes_sent": cwnd_cap_reached_sample["bytes_sent"],
            }
        )

    start_reason = None
    start_sample = None
    if slow_start_end_sample is not None:
        start_reason = "slow_start_exit"
        start_sample = slow_start_end_sample
    elif cwnd_cap_reached_sample is not None:
        start_reason = "cwnd_cap_reached"
        start_sample = cwnd_cap_reached_sample
    else:
        return summary

    elapsed = final_sample["timestamp"] - start_sample["timestamp"]
    post_slow_start_bytes = final_sample["bytes"] - start_sample["bytes"]

    if elapsed <= 0 or post_slow_start_bytes < 0:
        return summary

    summary.update(
        {
            "throughput_start_reason": start_reason,
            "post_slow_start_elapsed_seconds": elapsed,
            "post_slow_start_bytes": post_slow_start_bytes,
            "post_slow_start_mbit_per_second": (
                post_slow_start_bytes * 8.0 / elapsed / 1_000_000.0
            ),
            "post_slow_start_mib_per_second": (
                post_slow_start_bytes / elapsed / (1024.0 ** 2)
            ),
        }
    )

    return summary


def extract_ip_info(csv_path: Path, cwnd_limit=0) -> dict:
    phase_counts = {}
    rtt_total = 0
    rtt_count = 0
    row_count = 0
    first_timestamp = None
    last_timestamp = None
    min_timestamp = None
    max_timestamp = None
    seen_slow_start = False
    slow_start_end_sample = None
    cwnd_cap_reached_sample = None
    final_byte_sample = None

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        validate_columns(reader.fieldnames)

        for row in reader:
            row_count += 1

            phase = (row["phase"] or "unknown").lower()
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

            rtt = row["rtt"]
            if rtt:
                rtt_total += int(rtt)
                rtt_count += 1

            timestamp = row["timestamp"]
            if timestamp:
                timestamp_value = parse_float(timestamp)
                if timestamp_value is None:
                    continue

                if first_timestamp is None:
                    first_timestamp = timestamp_value
                last_timestamp = timestamp_value
                if min_timestamp is None or timestamp_value < min_timestamp:
                    min_timestamp = timestamp_value
                if max_timestamp is None or timestamp_value > max_timestamp:
                    max_timestamp = timestamp_value

            if phase == "slow_start":
                seen_slow_start = True

            byte_sample = new_byte_sample(row)
            if byte_sample is None:
                continue

            if phase != "slow_start" and seen_slow_start and slow_start_end_sample is None:
                slow_start_end_sample = byte_sample

            if (
                cwnd_limit > 0
                and cwnd_cap_reached_sample is None
                and byte_sample["cwnd"] is not None
                and byte_sample["cwnd"] >= cwnd_limit
            ):
                cwnd_cap_reached_sample = byte_sample

            final_byte_sample = byte_sample

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
        **summarize_post_slow_start(
            slow_start_end_sample,
            final_byte_sample,
            cwnd_cap_reached_sample,
            cwnd_limit,
        ),
    }


def write_json(output_path: Path, info: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(info, output_file, indent=2)
        output_file.write("\n")


def main() -> int:
    args = parse_args()
    if args.cwnd_limit < 0:
        print("--cwnd-limit must be non-negative", file=sys.stderr)
        return 1
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input CSV file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        info = extract_ip_info(input_path, args.cwnd_limit)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    write_json(output_path, info)
    print(f"Wrote JSON summary for {info['row_count']} CSV rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
