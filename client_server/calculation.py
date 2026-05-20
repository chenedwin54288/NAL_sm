#!/usr/bin/env python3

# With arrival-rate penalty (R_arrival > R_tbf):
# client_server/calculation.py \
#   --rate-mbit 250 \
#   --r-arrival-mbit 1000 \
#   --rtt-ms 0.4 \
#   --tbf-limit 2920b
#   --value-only or --json

# Without arrival-rate penalty (R_arrival = R_tbf):
# client_server/calculation.py \
#   --rate-mbit 250 \
#   --rtt-ms 0.4 \
#   --tbf-limit 2920b
#   --value-only or --json

# Reverse mode to infer R_arrival from an empirical optimal CWND:
# client_server/calculation.py \
#   --rate-mbit 500 \
#   --rtt-ms 0.4 \
#   --tbf-limit 50000b \
#   --optimal-cwnd 33 \
#   --value-only


import argparse
import json
import math
import re


DEFAULT_MSS_BYTES = 1460
DEFAULT_PACKET_BYTES = 1500


RATE_UNITS = {
    "bit": 1.0,
    "bits": 1.0,
    "bps": 1.0,
    "kbit": 1_000.0,
    "kbits": 1_000.0,
    "kbps": 1_000.0,
    "mbit": 1_000_000.0,
    "mbits": 1_000_000.0,
    "mbps": 1_000_000.0,
    "gbit": 1_000_000_000.0,
    "gbits": 1_000_000_000.0,
    "gbps": 1_000_000_000.0,
}

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
    "mib": 1024.0 ** 2,
    "g": 1_000_000_000.0,
    "gb": 1_000_000_000.0,
    "gbyte": 1_000_000_000.0,
    "gbytes": 1_000_000_000.0,
    "gib": 1024.0 ** 3,
}

TIME_UNITS = {
    "s": 1.0,
    "sec": 1.0,
    "secs": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "ms": 1e-3,
    "msec": 1e-3,
    "msecs": 1e-3,
    "us": 1e-6,
    "usec": 1e-6,
    "usecs": 1e-6,
}


def parse_number_with_unit(value: str, units: dict[str, float], default_unit: str) -> float:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid value: {value!r}")

    number = float(match.group(1))
    unit = (match.group(2) or default_unit).lower()
    if unit not in units:
        supported = ", ".join(sorted(unit for unit in units if unit))
        raise argparse.ArgumentTypeError(
            f"Unsupported unit {unit!r} in {value!r}; supported units: {supported}"
        )

    return number * units[unit]


def parse_rate(value: str) -> float:
    return parse_number_with_unit(value, RATE_UNITS, "mbit")


def parse_bytes(value: str) -> float:
    return parse_number_with_unit(value, BYTE_UNITS, "b")


def parse_seconds(value: str) -> float:
    return parse_number_with_unit(value, TIME_UNITS, "ms")


def floor_cwnd(bytes_budget: float, mss_bytes: int) -> int:
    return math.floor(bytes_budget / mss_bytes)


def calculate_cwnd(
    r_tbf_bps: float,
    rtt_seconds: float,
    q_config_bytes: float,
    mss_bytes: int,
    r_arrival_bps: float | None,
) -> dict:
    bdp_bytes = r_tbf_bps * rtt_seconds / 8.0
    arrival_bps = r_arrival_bps if r_arrival_bps is not None else r_tbf_bps
    q_tbf_bytes = max(0.0, (arrival_bps - r_tbf_bps) * rtt_seconds / 8.0)

    original_cwnd_raw = floor_cwnd(bdp_bytes + q_config_bytes - mss_bytes, mss_bytes)

    if q_tbf_bytes <= q_config_bytes:
        branch = "q_tbf <= q_config"
        q_effective_bytes = q_config_bytes - q_tbf_bytes
        usable_bdp_bytes = bdp_bytes
        arrival_aware_cwnd_raw = floor_cwnd(
            bdp_bytes + q_effective_bytes - mss_bytes,
            mss_bytes,
        )
    else:
        branch = "q_tbf > q_config"
        q_effective_bytes = 0.0
        usable_bdp_bytes = bdp_bytes * min(1.0, q_config_bytes / q_tbf_bytes)
        arrival_aware_cwnd_raw = floor_cwnd(usable_bdp_bytes - mss_bytes, mss_bytes)

    return {
        "r_tbf_mbit_per_second": r_tbf_bps / 1_000_000.0,
        "r_arrival_mbit_per_second": arrival_bps / 1_000_000.0,
        "rtt_ms": rtt_seconds * 1000.0,
        "mss_bytes": mss_bytes,
        "q_config_bytes": q_config_bytes,
        "bdp_bytes": bdp_bytes,
        "bdp_segments": bdp_bytes / mss_bytes,
        "q_tbf_bytes": q_tbf_bytes,
        "q_effective_bytes": q_effective_bytes,
        "usable_bdp_bytes": usable_bdp_bytes,
        "branch": branch,
        "original_cwnd_raw": original_cwnd_raw,
        "arrival_aware_cwnd_raw": arrival_aware_cwnd_raw,
        "original_cwnd": max(1, original_cwnd_raw),
        "arrival_aware_cwnd": max(1, arrival_aware_cwnd_raw),
    }


def rate_from_q_tbf(r_tbf_bps: float, rtt_seconds: float, q_tbf_bytes: float) -> float:
    return r_tbf_bps + (q_tbf_bytes * 8.0 / rtt_seconds)


def new_reverse_candidate(
    branch: str,
    r_tbf_bps: float,
    rtt_seconds: float,
    q_min_bytes: float,
    q_max_bytes: float,
) -> dict | None:
    if q_max_bytes < q_min_bytes:
        return None

    q_mid_bytes = (q_min_bytes + q_max_bytes) / 2.0
    r_min_bps = rate_from_q_tbf(r_tbf_bps, rtt_seconds, q_min_bytes)
    r_max_bps = rate_from_q_tbf(r_tbf_bps, rtt_seconds, q_max_bytes)
    r_mid_bps = rate_from_q_tbf(r_tbf_bps, rtt_seconds, q_mid_bytes)

    return {
        "branch": branch,
        "q_tbf_min_bytes": q_min_bytes,
        "q_tbf_max_bytes": q_max_bytes,
        "q_tbf_midpoint_bytes": q_mid_bytes,
        "r_arrival_min_mbit_per_second": r_min_bps / 1_000_000.0,
        "r_arrival_max_mbit_per_second": r_max_bps / 1_000_000.0,
        "r_arrival_midpoint_mbit_per_second": r_mid_bps / 1_000_000.0,
    }


def reverse_calculate_r_arrival(
    optimal_cwnd: int,
    r_tbf_bps: float,
    rtt_seconds: float,
    q_config_bytes: float,
    mss_bytes: int,
) -> dict:
    bdp_bytes = r_tbf_bps * rtt_seconds / 8.0
    candidates = []

    # Branch 1:
    #   cwnd = floor((BDP + Q_config - Q_tbf - MSS) / MSS)
    # Floor makes Q_tbf a range:
    #   BDP + Q_config - MSS - (cwnd + 1) * MSS < Q_tbf
    #   Q_tbf <= BDP + Q_config - MSS - cwnd * MSS
    branch_1_q_min = max(
        0.0,
        bdp_bytes + q_config_bytes - mss_bytes - (optimal_cwnd + 1) * mss_bytes,
    )
    branch_1_q_max = min(
        q_config_bytes,
        bdp_bytes + q_config_bytes - mss_bytes - optimal_cwnd * mss_bytes,
    )
    branch_1 = new_reverse_candidate(
        "q_tbf <= q_config",
        r_tbf_bps,
        rtt_seconds,
        branch_1_q_min,
        branch_1_q_max,
    )
    if branch_1 is not None:
        candidates.append(branch_1)

    # Branch 2:
    #   cwnd = floor(((BDP * Q_config / Q_tbf) - MSS) / MSS)
    # so:
    #   BDP * Q_config / ((cwnd + 2) * MSS) < Q_tbf
    #   Q_tbf <= BDP * Q_config / ((cwnd + 1) * MSS)
    if optimal_cwnd >= 0 and q_config_bytes > 0:
        branch_2_q_min = max(
            q_config_bytes,
            (bdp_bytes * q_config_bytes) / ((optimal_cwnd + 2) * mss_bytes),
        )
        branch_2_q_max = (
            bdp_bytes * q_config_bytes
        ) / ((optimal_cwnd + 1) * mss_bytes)
        branch_2 = new_reverse_candidate(
            "q_tbf > q_config",
            r_tbf_bps,
            rtt_seconds,
            branch_2_q_min,
            branch_2_q_max,
        )
        if branch_2 is not None:
            candidates.append(branch_2)

    result = {
        "mode": "reverse_r_arrival",
        "optimal_cwnd": optimal_cwnd,
        "r_tbf_mbit_per_second": r_tbf_bps / 1_000_000.0,
        "rtt_ms": rtt_seconds * 1000.0,
        "mss_bytes": mss_bytes,
        "q_config_bytes": q_config_bytes,
        "bdp_bytes": bdp_bytes,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }

    if candidates:
        result["r_arrival_estimate_mbit_per_second"] = candidates[0][
            "r_arrival_midpoint_mbit_per_second"
        ]
    else:
        result["r_arrival_estimate_mbit_per_second"] = None

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate optimal CWND from BDP, TBF queue, and optional R_arrival."
    )
    parser.add_argument(
        "--tbf-rate",
        "--rate",
        type=parse_rate,
        help="TBF bottleneck rate. Examples: 250Mbit, 500Mbit, 1Gbit. Bare numbers are Mbit/s.",
    )
    parser.add_argument(
        "--rate-mbit",
        type=float,
        default=None,
        help="TBF bottleneck rate in Mbit/s, matching run.sh naming.",
    )
    parser.add_argument(
        "--r-arrival",
        "--arrival-rate",
        type=parse_rate,
        default=None,
        help="Arrival/enqueue rate into TBF. Examples: 1000Mbit, 1Gbit. Omit to use R_tbf.",
    )
    parser.add_argument(
        "--r-arrival-mbit",
        type=float,
        default=None,
        help="Arrival/enqueue rate into TBF in Mbit/s.",
    )
    parser.add_argument(
        "--rtt",
        type=parse_seconds,
        help="Base RTT. Examples: 0.4ms, 400us. Bare numbers are ms.",
    )
    parser.add_argument(
        "--rtt-ms",
        type=float,
        default=None,
        help="Base RTT in milliseconds, matching run.sh naming.",
    )
    parser.add_argument(
        "--queue",
        "--tbf-limit",
        type=parse_bytes,
        default=None,
        help="Configured TBF queue limit in bytes. Examples: 15000b, 50000b.",
    )
    parser.add_argument(
        "--queue-packets",
        type=float,
        default=None,
        help="Configured TBF queue as packet count. Converted with --packet-bytes.",
    )
    parser.add_argument(
        "--packet-bytes",
        type=int,
        default=DEFAULT_PACKET_BYTES,
        help=f"Packet size used for --queue-packets (default: {DEFAULT_PACKET_BYTES}).",
    )
    parser.add_argument(
        "--mss",
        type=int,
        default=DEFAULT_MSS_BYTES,
        help=f"TCP MSS used for cwnd segments (default: {DEFAULT_MSS_BYTES}).",
    )
    parser.add_argument(
        "--optimal-cwnd",
        type=int,
        default=None,
        help="Reverse mode: infer R_arrival from an empirical optimal CWND.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON.",
    )
    parser.add_argument(
        "--value-only",
        action="store_true",
        help="Print only the arrival-aware CWND value.",
    )
    args = parser.parse_args()

    if args.tbf_rate is None and args.rate_mbit is None:
        parser.error("Specify either --tbf-rate/--rate or --rate-mbit")

    if args.tbf_rate is not None and args.rate_mbit is not None:
        parser.error("Specify only one of --tbf-rate/--rate or --rate-mbit")

    if args.r_arrival is not None and args.r_arrival_mbit is not None:
        parser.error("Specify only one of --r-arrival/--arrival-rate or --r-arrival-mbit")

    if args.optimal_cwnd is not None and (
        args.r_arrival is not None or args.r_arrival_mbit is not None
    ):
        parser.error("Do not specify --r-arrival with --optimal-cwnd reverse mode")

    if args.rtt is None and args.rtt_ms is None:
        parser.error("Specify either --rtt or --rtt-ms")

    if args.rtt is not None and args.rtt_ms is not None:
        parser.error("Specify only one of --rtt or --rtt-ms")

    if args.queue is None and args.queue_packets is None:
        parser.error("Specify either --queue/--tbf-limit or --queue-packets")

    if args.queue is not None and args.queue_packets is not None:
        parser.error("Specify only one of --queue/--tbf-limit or --queue-packets")

    if args.mss <= 0:
        parser.error("--mss must be greater than 0")

    if args.packet_bytes <= 0:
        parser.error("--packet-bytes must be greater than 0")

    if args.optimal_cwnd is not None and args.optimal_cwnd < 0:
        parser.error("--optimal-cwnd must be non-negative")

    return args


def print_human_readable(result: dict) -> None:
    print("Inputs")
    print(f"  R_tbf:      {result['r_tbf_mbit_per_second']:.3f} Mbit/s")
    print(f"  R_arrival:  {result['r_arrival_mbit_per_second']:.3f} Mbit/s")
    print(f"  RTT_base:   {result['rtt_ms']:.6g} ms")
    print(f"  MSS:        {result['mss_bytes']} B")
    print(f"  Q_config:   {result['q_config_bytes']:.2f} B")
    print()
    print("Derived")
    print(f"  BDP:        {result['bdp_bytes']:.2f} B ({result['bdp_segments']:.2f} MSS)")
    print(f"  Q_tbf:      {result['q_tbf_bytes']:.2f} B")
    print(f"  Branch:     {result['branch']}")
    print(f"  Q_effective:{result['q_effective_bytes']:.2f} B")
    print(f"  usable_bdp: {result['usable_bdp_bytes']:.2f} B")
    print()
    print("CWND")
    print(f"  original_cwnd:      {result['original_cwnd']}")
    print(f"  arrival_aware_cwnd: {result['arrival_aware_cwnd']}")
    if (
        result["original_cwnd"] != result["original_cwnd_raw"]
        or result["arrival_aware_cwnd"] != result["arrival_aware_cwnd_raw"]
    ):
        print()
        print("Raw formula values before min-cwnd clamp")
        print(f"  original_cwnd_raw:      {result['original_cwnd_raw']}")
        print(f"  arrival_aware_cwnd_raw: {result['arrival_aware_cwnd_raw']}")


def print_reverse_human_readable(result: dict) -> None:
    print("Inputs")
    print(f"  optimal_cwnd: {result['optimal_cwnd']}")
    print(f"  R_tbf:        {result['r_tbf_mbit_per_second']:.3f} Mbit/s")
    print(f"  RTT_base:     {result['rtt_ms']:.6g} ms")
    print(f"  MSS:          {result['mss_bytes']} B")
    print(f"  Q_config:     {result['q_config_bytes']:.2f} B")
    print()
    print("Derived")
    print(f"  BDP:          {result['bdp_bytes']:.2f} B")

    if not result["candidates"]:
        print()
        print("No valid R_arrival range for this CWND under the current model.")
        return

    print()
    print("Reverse R_arrival candidates")
    for candidate in result["candidates"]:
        print(f"  Branch: {candidate['branch']}")
        print(
            "    Q_tbf:      "
            f"{candidate['q_tbf_min_bytes']:.2f} .. "
            f"{candidate['q_tbf_max_bytes']:.2f} B"
        )
        print(
            "    R_arrival:  "
            f"{candidate['r_arrival_min_mbit_per_second']:.3f} .. "
            f"{candidate['r_arrival_max_mbit_per_second']:.3f} Mbit/s"
        )
        print(
            "    midpoint:   "
            f"{candidate['r_arrival_midpoint_mbit_per_second']:.3f} Mbit/s"
        )


def main() -> int:
    args = parse_args()
    r_tbf_bps = (
        args.tbf_rate
        if args.tbf_rate is not None
        else args.rate_mbit * 1_000_000.0
    )
    r_arrival_bps = args.r_arrival
    if r_arrival_bps is None and args.r_arrival_mbit is not None:
        r_arrival_bps = args.r_arrival_mbit * 1_000_000.0
    rtt_seconds = args.rtt if args.rtt is not None else args.rtt_ms / 1000.0
    q_config_bytes = (
        args.queue
        if args.queue is not None
        else args.queue_packets * args.packet_bytes
    )
    if args.optimal_cwnd is not None:
        result = reverse_calculate_r_arrival(
            optimal_cwnd=args.optimal_cwnd,
            r_tbf_bps=r_tbf_bps,
            rtt_seconds=rtt_seconds,
            q_config_bytes=q_config_bytes,
            mss_bytes=args.mss,
        )
    else:
        result = calculate_cwnd(
            r_tbf_bps=r_tbf_bps,
            rtt_seconds=rtt_seconds,
            q_config_bytes=q_config_bytes,
            mss_bytes=args.mss,
            r_arrival_bps=r_arrival_bps,
        )

    if args.value_only:
        if args.optimal_cwnd is not None:
            print(result["r_arrival_estimate_mbit_per_second"])
        else:
            print(result["arrival_aware_cwnd"])
    elif args.json:
        print(json.dumps(result, indent=2))
    elif args.optimal_cwnd is not None:
        print_reverse_human_readable(result)
    else:
        print_human_readable(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
