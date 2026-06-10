#!/usr/bin/env python3

import argparse
import csv
import json
import math
import os
import socket
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from arrival_estimation import (
    ProbeSample,
    compute_queue_delay_samples,
    estimate_arrival_and_rwnd,
)
from probe_protocol import (
    FRAME_TYPE_PROBE,
    FRAME_TYPE_STOP,
    PROBE_HEADER_SIZE,
    unpack_header,
)


STOP_COMMAND = b"CUMULATIVE_STOP\n"
DEFAULT_HOST = "192.168.88.254"
DEFAULT_PORT = 9001
DEFAULT_CHUNK_SIZE = 64 * 1024 #determines the recv() buffer size, when big => less sampling
DEFAULT_MSS_BYTES = 1460
DEFAULT_RTT_MS = 400.0
DEFAULT_ESTIMATION_WINDOW_SIZE = 20
DEFAULT_PROBE_FORMAT = "framed"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "cumulative_arrival.csv")


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
    "kibit": 1024.0,
    "mibit": 1024.0 ** 2,
    "gibit": 1024.0 ** 3,
    "kib": 1024.0,
    "mib": 1024.0 ** 2,
    "gib": 1024.0 ** 3,
}

BYTE_UNITS = {
    "": 1.0,
    "b": 1.0,
    "byte": 1.0,
    "bytes": 1.0,
    "k": 1_000.0,
    "kb": 1_000.0,
    "kib": 1024.0,
    "m": 1_000_000.0,
    "mb": 1_000_000.0,
    "mib": 1024.0 ** 2,
    "g": 1_000_000_000.0,
    "gb": 1_000_000_000.0,
    "gib": 1024.0 ** 3,
}


def parse_number_with_unit(value, units, default_unit):
    text = str(value).strip().lower()
    for suffix in ("/second", "/sec", "/s"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break

    number = []
    unit = []

    for char in text:
        if char.isdigit() or char == ".":
            if unit:
                raise argparse.ArgumentTypeError(f"Invalid value: {value!r}")
            number.append(char)
        elif char.isalpha():
            unit.append(char)
        elif char.isspace():
            continue
        else:
            raise argparse.ArgumentTypeError(f"Invalid value: {value!r}")

    if not number:
        raise argparse.ArgumentTypeError(f"Invalid value: {value!r}")

    unit_name = "".join(unit) or default_unit
    if unit_name not in units:
        supported = ", ".join(sorted(key for key in units if key))
        raise argparse.ArgumentTypeError(
            f"Unsupported unit {unit_name!r}; supported units: {supported}"
        )

    return float("".join(number)) * units[unit_name]


def parse_rate_bits_per_second(value):
    return parse_number_with_unit(value, RATE_UNITS, "mbit")


def parse_bytes(value):
    return int(parse_number_with_unit(value, BYTE_UNITS, "b"))


def connect(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        return sock
    except Exception:
        sock.close()
        raise


def new_sample(
    sample_index,
    timestamp,
    elapsed,
    previous_elapsed,
    byte_count,
    cumulative,
):
    delta_seconds = elapsed - previous_elapsed
    instant_mbit = None
    if delta_seconds > 0:
        instant_mbit = byte_count * 8.0 / delta_seconds / 1_000_000.0

    average_mbit = None
    if elapsed > 0:
        average_mbit = cumulative * 8.0 / elapsed / 1_000_000.0

    return {
        "sample": sample_index,
        "timestamp": timestamp,
        "elapsed_seconds": elapsed,
        "delta_seconds": delta_seconds,
        "bytes_received": byte_count,
        "cumulative_bytes": cumulative,
        "instant_throughput_mbit": instant_mbit,
        "average_throughput_mbit": average_mbit,
    }


def new_probe_record_sample(
    sample_index,
    seq,
    send_timestamp_ns,
    recv_timestamp_ns,
    elapsed,
    previous_elapsed,
    payload_size,
    cumulative,
):
    sample = new_sample(
        sample_index=sample_index,
        timestamp=recv_timestamp_ns / 1_000_000_000.0,
        elapsed=elapsed,
        previous_elapsed=previous_elapsed,
        byte_count=payload_size,
        cumulative=cumulative,
    )
    sample.update(
        {
            "seq": seq,
            "send_timestamp": send_timestamp_ns / 1_000_000_000.0,
            "send_timestamp_ns": send_timestamp_ns,
            "recv_timestamp": recv_timestamp_ns / 1_000_000_000.0,
            "recv_timestamp_ns": recv_timestamp_ns,
            "payload_size": payload_size,
        }
    )
    return sample


def receive_raw_until_stop(sock, recv_size):
    samples = []
    pending = b""
    cumulative = 0
    previous_elapsed = 0.0
    start = time.monotonic()

    def add_payload_sample(payload, timestamp, elapsed):
        nonlocal cumulative, previous_elapsed

        if not payload:
            return

        cumulative += len(payload)
        samples.append(
            new_sample(
                sample_index=len(samples) + 1,
                timestamp=timestamp,
                elapsed=elapsed,
                previous_elapsed=previous_elapsed,
                byte_count=len(payload),
                cumulative=cumulative,
            )
        )
        previous_elapsed = elapsed

    while True:
        data = sock.recv(recv_size)
        timestamp = time.time()
        elapsed = time.monotonic() - start

        if not data:
            add_payload_sample(pending, timestamp, elapsed)
            return samples, cumulative, False

        pending += data
        stop_index = pending.find(STOP_COMMAND)
        if stop_index != -1:
            add_payload_sample(pending[:stop_index], timestamp, elapsed)
            return samples, cumulative, True

        keep = len(STOP_COMMAND) - 1
        if len(pending) > keep:
            add_payload_sample(pending[:-keep], timestamp, elapsed)
            pending = pending[-keep:]


def receive_framed_until_stop(sock, recv_size):
    samples = []
    pending = bytearray()
    cumulative = 0
    previous_elapsed = 0.0
    start = time.monotonic()

    while True:
        data = sock.recv(recv_size)
        recv_timestamp_ns = time.time_ns()
        elapsed = time.monotonic() - start

        if not data:
            return samples, cumulative, False

        pending.extend(data)
        while len(pending) >= PROBE_HEADER_SIZE:
            header = bytes(pending[:PROBE_HEADER_SIZE])
            frame_type, seq, send_timestamp_ns, payload_size = unpack_header(header)
            frame_size = PROBE_HEADER_SIZE + payload_size
            if len(pending) < frame_size:
                break

            del pending[:PROBE_HEADER_SIZE]
            if payload_size:
                del pending[:payload_size]

            if frame_type == FRAME_TYPE_STOP:
                return samples, cumulative, True

            if frame_type != FRAME_TYPE_PROBE:
                raise ValueError(f"unsupported probe frame type: {frame_type}")

            cumulative += payload_size
            samples.append(
                new_probe_record_sample(
                    sample_index=len(samples) + 1,
                    seq=seq,
                    send_timestamp_ns=send_timestamp_ns,
                    recv_timestamp_ns=recv_timestamp_ns,
                    elapsed=elapsed,
                    previous_elapsed=previous_elapsed,
                    payload_size=payload_size,
                    cumulative=cumulative,
                )
            )
            previous_elapsed = elapsed


def receive_until_stop(sock, recv_size, probe_format):
    if probe_format == "framed":
        return receive_framed_until_stop(sock, recv_size)
    if probe_format == "raw":
        return receive_raw_until_stop(sock, recv_size)
    raise ValueError(f"unsupported probe format: {probe_format}")


SAMPLE_FIELDNAMES = [
    "sample",
    "timestamp",
    "elapsed_seconds",
    "delta_seconds",
    "bytes_received",
    "cumulative_bytes",
    "instant_throughput_mbit",
    "average_throughput_mbit",
    "seq",
    "send_timestamp",
    "send_timestamp_ns",
    "recv_timestamp",
    "recv_timestamp_ns",
    "payload_size",
    "owd_seconds",
    "qdelay_seconds",
    "qbytes",
]


def write_samples(path, samples):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=SAMPLE_FIELDNAMES,
            extrasaction="ignore",
        )
        writer.writeheader()
        for sample in samples:
            writer.writerow({field: sample.get(field) for field in SAMPLE_FIELDNAMES})


def write_summary(path, summary):
    if path is None:
        return

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2)
        summary_file.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run the arrival probe client. In framed mode it records "
            "timestamped probe records and estimates the enqueue rate into "
            "the server-side TBF queue."
        )
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Server host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--recv-size",
        type=parse_bytes,
        default=DEFAULT_CHUNK_SIZE,
        help="Socket recv size, for example 64KiB (default: 64KiB)",
    )
    parser.add_argument(
        "--probe-format",
        choices=("framed", "raw"),
        default=DEFAULT_PROBE_FORMAT,
        help=(
            "framed reads timestamped probe records; raw reads the legacy "
            f"byte stream (default: {DEFAULT_PROBE_FORMAT})"
        ),
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT_FILE,
        help=f"CSV path for cumulative samples (default: {DEFAULT_OUTPUT_FILE})",
    )
    parser.add_argument(
        "--summary-file",
        default=None,
        help="Write probe summary JSON to this path",
    )
    parser.add_argument(
        "--rtt-ms",
        type=float,
        default=DEFAULT_RTT_MS,
        help=(
            "RTT_base in milliseconds for queue-delay and rwnd calculation "
            f"(default: {DEFAULT_RTT_MS}, matching 1.2s = 3 RTTs)"
        ),
    )
    parser.add_argument(
        "--base-owd-ms",
        type=float,
        default=None,
        help=(
            "Known one-way base delay in milliseconds. If omitted, the client "
            "uses RTT_base / 2."
        ),
    )
    parser.add_argument(
        "--tbf-rate",
        type=parse_rate_bits_per_second,
        default=None,
        help=(
            "Known TBF service rate, for example 100Mbit. Bare numbers are "
            "Mbit/s. Required with --tbf-limit for arrival-aware rwnd."
        ),
    )
    parser.add_argument(
        "--tbf-limit",
        "--queue",
        type=parse_bytes,
        default=None,
        help=(
            "Known TBF queue size Q_config in bytes, for example 6250b. "
            "Required with --tbf-rate for arrival-aware rwnd."
        ),
    )
    parser.add_argument(
        "--mss-bytes",
        type=int,
        default=DEFAULT_MSS_BYTES,
        help=f"MSS bytes for segment display (default: {DEFAULT_MSS_BYTES})",
    )
    parser.add_argument(
        "--estimation-window-size",
        type=int,
        default=DEFAULT_ESTIMATION_WINDOW_SIZE,
        help=(
            "Sliding-window sample count for the queue-growth regression "
            f"(default: {DEFAULT_ESTIMATION_WINDOW_SIZE})"
        ),
    )
    parser.add_argument(
        "--rwnd-gain",
        type=float,
        default=1.0,
        help=(
            "Legacy raw/cumulative multiplier applied to measured BDP "
            "(default: 1.0). Ignored by the framed TBF estimator."
        ),
    )
    args = parser.parse_args()

    if args.port <= 0:
        parser.error("--port must be positive")
    if args.recv_size <= 0:
        parser.error("--recv-size must be positive")
    if args.rtt_ms <= 0:
        parser.error("--rtt-ms must be positive")
    if args.base_owd_ms is not None and args.base_owd_ms < 0:
        parser.error("--base-owd-ms must be non-negative")
    if (args.tbf_rate is None) != (args.tbf_limit is None):
        parser.error("set --tbf-rate and --tbf-limit together")
    if args.tbf_rate is not None and args.probe_format != "framed":
        parser.error("arrival-aware rwnd requires --probe-format framed")
    if args.mss_bytes <= 0:
        parser.error("--mss-bytes must be positive")
    if args.estimation_window_size <= 1:
        parser.error("--estimation-window-size must be greater than 1")
    if args.rwnd_gain <= 0:
        parser.error("--rwnd-gain must be positive")

    return args


def probe_samples_from_rows(samples):
    return [
        ProbeSample(
            seq=int(sample["seq"]),
            send_timestamp=float(sample["send_timestamp"]),
            recv_timestamp=float(sample["recv_timestamp"]),
            payload_size=int(sample["payload_size"]),
        )
        for sample in samples
        if sample.get("seq") is not None
    ]


def add_queue_fields_to_rows(
    samples,
    probe_samples,
    r_tbf_bytes_per_second,
    rtt_base_seconds,
    base_owd_seconds,
):
    queue_samples = compute_queue_delay_samples(
        samples=probe_samples,
        r_tbf_bytes_per_second=r_tbf_bytes_per_second,
        rtt_base_seconds=rtt_base_seconds,
        base_owd_seconds=base_owd_seconds,
    )
    for row, queue_sample in zip(samples, queue_samples):
        row["owd_seconds"] = queue_sample.owd_seconds
        row["qdelay_seconds"] = queue_sample.qdelay_seconds
        row["qbytes"] = queue_sample.qbytes


def main():
    args = parse_args()

    with connect(args.host, args.port) as sock:
        print(f"Connected to {args.host}:{args.port}")
        samples, received, got_stop = receive_until_stop(
            sock,
            args.recv_size,
            args.probe_format,
        )

    elapsed = samples[-1]["elapsed_seconds"] if samples else 0.0
    average_bytes_per_second = received / elapsed if elapsed > 0 else 0.0
    average_mbit = average_bytes_per_second * 8.0 / 1_000_000.0
    arrival_result = None

    if args.tbf_rate is not None:
        r_tbf_bytes_per_second = args.tbf_rate / 8.0
        rtt_base_seconds = args.rtt_ms / 1000.0
        base_owd_seconds = (
            args.base_owd_ms / 1000.0 if args.base_owd_ms is not None else None
        )
        probe_samples = probe_samples_from_rows(samples)
        add_queue_fields_to_rows(
            samples=samples,
            probe_samples=probe_samples,
            r_tbf_bytes_per_second=r_tbf_bytes_per_second,
            rtt_base_seconds=rtt_base_seconds,
            base_owd_seconds=base_owd_seconds,
        )
        arrival_result = estimate_arrival_and_rwnd(
            samples=probe_samples,
            r_tbf_bytes_per_second=r_tbf_bytes_per_second,
            rtt_base_seconds=rtt_base_seconds,
            q_config_bytes=args.tbf_limit,
            mss_bytes=args.mss_bytes,
            base_owd_seconds=base_owd_seconds,
            window_size=args.estimation_window_size,
        )
        rwnd_bytes = int(arrival_result["rwnd_bytes"])
        rwnd_segments = int(arrival_result["cwnd_segments"])
    else:
        rwnd_bytes = int(
            math.ceil(
                average_bytes_per_second
                * (args.rtt_ms / 1000.0)
                * args.rwnd_gain
            )
        )
        rwnd_segments = (
            int(math.ceil(rwnd_bytes / args.mss_bytes)) if rwnd_bytes > 0 else 0
        )

    write_samples(args.output_file, samples)

    print(f"Received {received} bytes in {elapsed:.6f}s ({average_mbit:.3f} Mbit/s)")
    print(f"Wrote cumulative samples to {args.output_file}")
    if arrival_result is not None:
        print(
            "Estimated R_arrival: "
            f"{arrival_result['r_arrival_bytes_per_second'] * 8.0 / 1_000_000:.3f} "
            "Mbit/s"
        )
        print(
            "Queue-growth beta: "
            f"{arrival_result['beta_queue_growth_rate'] * 8.0 / 1_000_000:.3f} "
            "Mbit/s "
            f"(samples={arrival_result['sample_count']}, "
            f"valid={arrival_result['valid_estimate']}, "
            f"loss={arrival_result['loss_observed']}, "
            f"saturation={arrival_result['saturation_observed']})"
        )
    print(
        "Recommended rwnd: "
        f"{rwnd_bytes} bytes ({rwnd_segments} MSS segments, RTT_base={args.rtt_ms:g} ms)"
    )
    print(
        "Normal client command: "
        f"python3 client/client.py --rwnd-bytes {rwnd_bytes}"
    )

    if not got_stop:
        print("Warning: connection closed before cumulative STOP signal was received")

    summary = {
        "server_host": args.host,
        "server_port": args.port,
        "probe_format": args.probe_format,
        "timestamp_units": (
            "send_timestamp and recv_timestamp are seconds since Unix epoch; "
            "framed wire timestamps are nanoseconds since Unix epoch"
        ),
        "received_bytes": received,
        "elapsed_seconds": elapsed,
        "average_bytes_per_second": average_bytes_per_second,
        "average_mbit_per_second": average_mbit,
        "received_sample_count": len(samples),
        "output_file": args.output_file,
        "got_stop": got_stop,
        "rtt_ms": args.rtt_ms,
        "base_owd_ms": args.base_owd_ms,
        "mss_bytes": args.mss_bytes,
        "rwnd_gain": args.rwnd_gain,
        "recommended_rwnd_bytes": rwnd_bytes,
        "recommended_rwnd_segments": rwnd_segments,
    }
    if arrival_result is not None:
        summary.update(arrival_result)
        summary["r_arrival_mbit_per_second"] = (
            arrival_result["r_arrival_bytes_per_second"] * 8.0 / 1_000_000.0
        )
        summary["beta_queue_growth_mbit_per_second"] = (
            arrival_result["beta_queue_growth_rate"] * 8.0 / 1_000_000.0
        )

    write_summary(args.summary_file, summary)


if __name__ == "__main__":
    main()
