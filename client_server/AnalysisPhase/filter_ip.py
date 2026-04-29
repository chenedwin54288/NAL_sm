#!/usr/bin/env python3

# Example command:
#    python3 AnalysisPhase/filter_ip.py \
#      -i AnalysisPhase/test_context.txt \
#      -o AnalysisPhase/filtered_context.csv
#    
#   python3 AnalysisPhase/filter_ip.py \
#      -i AnalysisPhase/test_context.txt \
#      -o AnalysisPhase/filtered_56988.csv \
#      --ip 128.178.122.39 \
#      --port 56988


import argparse
import csv
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR.parent / "Server" / "server_sub_process_1" / "context.txt"
DEFAULT_OUTPUT = SCRIPT_DIR / "filtered_context.csv"

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

RTT_PATTERN = re.compile(r"\brtt=(?P<rtt>\d+)\b")
SSTHRESH_PATTERN = re.compile(r"\bssthresh=(?P<ssthresh>\d+)\b")
CA_STATE_PATTERN = re.compile(r"\bca_state=(?P<ca_state>[a-zA-Z_]+)(?:\(\d+\))?\b")
CA_PHASE_PATTERN = re.compile(r"\bphase=(?P<phase>[a-zA-Z_]+)(?:\(\d+\))?\b")

FIELDNAMES = [
    "line_number",
    "timestamp",
    "cwnd",
    "ip",
    "port",
    "rtt",
    "ssthresh",
    "phase",
    "ca_state",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter mixed kernel logs into structured cwnd CSV rows."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=str(DEFAULT_INPUT),
        help=f"Path to mixed context log file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Path to output CSV file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument("--ip", default=None, help="Only include this destination IP")
    parser.add_argument("--port", type=int, default=None, help="Only include this destination port")
    return parser.parse_args()


def optional_group(pattern: re.Pattern, line: str, group_name: str) -> str:
    match = pattern.search(line)
    if not match:
        return ""
    return match.group(group_name)


def parse_line(line_number: int, line: str):
    clean_line = line.rstrip("\n")
    match = LOG_PATTERN.match(clean_line)
    if not match:
        return None

    return {
        "line_number": line_number,
        "timestamp": match.group("timestamp"),
        "cwnd": match.group("cwnd"),
        "ip": match.group("ip"),
        "port": match.group("port"),
        "rtt": optional_group(RTT_PATTERN, clean_line, "rtt"),
        "ssthresh": optional_group(SSTHRESH_PATTERN, clean_line, "ssthresh"),
        "phase": optional_group(CA_PHASE_PATTERN, clean_line, "phase"),
        "ca_state": optional_group(CA_STATE_PATTERN, clean_line, "ca_state"),
    }


def filter_context(input_path: Path, output_path: Path, ip: str | None, port: int | None) -> int:
    rows_written = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as input_file, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDNAMES)
        writer.writeheader()

        for line_number, line in enumerate(input_file, start=1):
            row = parse_line(line_number, line)
            if row is None:
                continue

            if ip is not None and row["ip"] != ip:
                continue

            if port is not None and int(row["port"]) != port:
                continue

            writer.writerow(row)
            rows_written += 1

    return rows_written


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input log file not found: {input_path}", file=sys.stderr)
        return 1

    rows_written = filter_context(input_path, output_path, args.ip, args.port)
    print(f"Wrote {rows_written} matching rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())