#!/usr/bin/env python3

import argparse
import csv
import json
import math
import os
import socket
import time


STOP_COMMAND = b"CUMULATIVE_STOP\n"
DEFAULT_HOST = "192.168.88.254"
DEFAULT_PORT = 9001
DEFAULT_CHUNK_SIZE = 64 * 1024
DEFAULT_MSS_BYTES = 1460
DEFAULT_RTT_MS = 400.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "cumulative_arrival.csv")


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


def parse_bytes(value):
    text = str(value).strip().lower()
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

    unit_name = "".join(unit) or "b"
    if unit_name not in BYTE_UNITS:
        supported = ", ".join(sorted(key for key in BYTE_UNITS if key))
        raise argparse.ArgumentTypeError(
            f"Unsupported unit {unit_name!r}; supported units: {supported}"
        )

    return int(float("".join(number)) * BYTE_UNITS[unit_name])


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


def receive_until_stop(sock, recv_size):
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


def write_samples(path, samples):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "sample",
                "timestamp",
                "elapsed_seconds",
                "delta_seconds",
                "bytes_received",
                "cumulative_bytes",
                "instant_throughput_mbit",
                "average_throughput_mbit",
            ],
        )
        writer.writeheader()
        for sample in samples:
            writer.writerow(sample)


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
            "Run the cumulative-byte arrival probe client. It timestamps each "
            "TCP recv event and writes cumulative arrival samples to CSV."
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
            "RTT in milliseconds for recommended rwnd calculation "
            f"(default: {DEFAULT_RTT_MS}, matching 1.2s = 3 RTTs)"
        ),
    )
    parser.add_argument(
        "--mss-bytes",
        type=int,
        default=DEFAULT_MSS_BYTES,
        help=f"MSS bytes for segment display (default: {DEFAULT_MSS_BYTES})",
    )
    parser.add_argument(
        "--rwnd-gain",
        type=float,
        default=1.0,
        help="Multiplier applied to measured BDP before reporting rwnd (default: 1.0)",
    )
    args = parser.parse_args()

    if args.port <= 0:
        parser.error("--port must be positive")
    if args.recv_size <= 0:
        parser.error("--recv-size must be positive")
    if args.rtt_ms <= 0:
        parser.error("--rtt-ms must be positive")
    if args.mss_bytes <= 0:
        parser.error("--mss-bytes must be positive")
    if args.rwnd_gain <= 0:
        parser.error("--rwnd-gain must be positive")

    return args


def main():
    args = parse_args()

    with connect(args.host, args.port) as sock:
        print(f"Connected to {args.host}:{args.port}")
        samples, received, got_stop = receive_until_stop(sock, args.recv_size)

    write_samples(args.output_file, samples)

    elapsed = samples[-1]["elapsed_seconds"] if samples else 0.0
    average_bytes_per_second = received / elapsed if elapsed > 0 else 0.0
    average_mbit = average_bytes_per_second * 8.0 / 1_000_000.0
    rwnd_bytes = int(
        math.ceil(
            average_bytes_per_second
            * (args.rtt_ms / 1000.0)
            * args.rwnd_gain
        )
    )
    rwnd_segments = int(math.ceil(rwnd_bytes / args.mss_bytes)) if rwnd_bytes > 0 else 0

    print(f"Received {received} bytes in {elapsed:.6f}s ({average_mbit:.3f} Mbit/s)")
    print(f"Wrote cumulative samples to {args.output_file}")
    print(
        "Recommended rwnd: "
        f"{rwnd_bytes} bytes ({rwnd_segments} MSS segments, RTT={args.rtt_ms:g} ms)"
    )
    print(
        "Normal client command: "
        f"python3 client/client.py --rwnd-bytes {rwnd_bytes}"
    )

    if not got_stop:
        print("Warning: connection closed before cumulative STOP signal was received")

    write_summary(
        args.summary_file,
        {
            "server_host": args.host,
            "server_port": args.port,
            "received_bytes": received,
            "elapsed_seconds": elapsed,
            "average_bytes_per_second": average_bytes_per_second,
            "average_mbit_per_second": average_mbit,
            "sample_count": len(samples),
            "output_file": args.output_file,
            "got_stop": got_stop,
            "rtt_ms": args.rtt_ms,
            "mss_bytes": args.mss_bytes,
            "rwnd_gain": args.rwnd_gain,
            "recommended_rwnd_bytes": rwnd_bytes,
            "recommended_rwnd_segments": rwnd_segments,
        },
    )


if __name__ == "__main__":
    main()
