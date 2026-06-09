#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from result_parser import DEFAULT_INPUT, REPORT_DIR, parse_results, write_csv


def main() -> int:
    rows = parse_results(DEFAULT_INPUT)
    output = REPORT_DIR / "generated" / "all_results.csv"
    write_csv(rows, output)
    print(f"Wrote {len(rows)} rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

