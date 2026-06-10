#!/usr/bin/env python3

import argparse
import json
import math
import os
import socket
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from probe_protocol import pack_probe_header, pack_stop_header


STOP_COMMAND = b"CUMULATIVE_STOP\n"
DEFAULT_HOST = "192.168.88.254"
DEFAULT_PORT = 9001
DEFAULT_RATE = "1Gib"
DEFAULT_DURATION_SECONDS = 10.0
DEFAULT_CHUNK_SIZE = 1024 * 1024
DEFAULT_SEND_MODE = "paced"
DEFAULT_PROBE_FORMAT = "framed"
SO_MAX_PACING_RATE = getattr(socket, "SO_MAX_PACING_RATE", 47)


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


def set_socket_pacing(sock, bytes_per_second):
    if bytes_per_second <= 0:
        return False

    try:
        sock.setsockopt(socket.SOL_SOCKET, SO_MAX_PACING_RATE, int(bytes_per_second))
    except OSError as error:
        print(f"Warning: could not set SO_MAX_PACING_RATE: {error}")
        return False

    return True


def send_paced(conn, total_bytes, rate_bytes_per_second, chunk_size):
    sent = 0
    block = b"\0" * chunk_size
    start = time.monotonic()

    while sent < total_bytes:
        to_send = min(chunk_size, total_bytes - sent)
        conn.sendall(block[:to_send])
        sent += to_send

        target_elapsed = sent / rate_bytes_per_second
        actual_elapsed = time.monotonic() - start
        sleep_seconds = target_elapsed - actual_elapsed
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    return sent, time.monotonic() - start


def send_bulk(conn, total_bytes, chunk_size):
    sent = 0
    block = b"\0" * chunk_size
    start = time.monotonic()

    while sent < total_bytes:
        to_send = min(chunk_size, total_bytes - sent)
        conn.sendall(block[:to_send])
        sent += to_send

    return sent, time.monotonic() - start


def send_framed_probe_train(
    conn,
    total_payload_bytes,
    rate_bytes_per_second,
    payload_size,
    send_mode,
):
    sent_payload = 0
    seq = 0
    block = b"\0" * payload_size
    start = time.monotonic()

    while sent_payload < total_payload_bytes:
        to_send = min(payload_size, total_payload_bytes - sent_payload)
        header = pack_probe_header(
            seq=seq,
            send_timestamp_ns=time.time_ns(),
            payload_size=to_send,
        )
        conn.sendall(header + block[:to_send])
        sent_payload += to_send
        seq += 1

        if send_mode == "paced":
            target_elapsed = sent_payload / rate_bytes_per_second
            actual_elapsed = time.monotonic() - start
            sleep_seconds = target_elapsed - actual_elapsed
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    elapsed = time.monotonic() - start
    conn.sendall(pack_stop_header(seq=seq))
    return sent_payload, elapsed, seq


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
            "Run the cumulative-byte arrival probe server. It sends generated "
            "bytes at a configured rate for a configured duration."
        )
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Bind host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Bind port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--rate",
        type=parse_rate_bits_per_second,
        default=parse_rate_bits_per_second(DEFAULT_RATE),
        help=f"Probe send rate, for example 20Mbit or 1Gbit (default: {DEFAULT_RATE})",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION_SECONDS,
        help=(
            "Probe duration in seconds. In paced mode this is the intended "
            "wall-clock duration; in bulk mode it is used with --rate to "
            "derive the byte budget. "
            f"(default: {DEFAULT_DURATION_SECONDS})"
        ),
    )
    parser.add_argument(
        "--send-mode",
        choices=("paced", "bulk"),
        default=DEFAULT_SEND_MODE,
        help=(
            "paced sleeps between writes to match --rate; bulk sends like "
            f"Server/server.py with no application sleep (default: {DEFAULT_SEND_MODE})"
        ),
    )
    parser.add_argument(
        "--probe-format",
        choices=("framed", "raw"),
        default=DEFAULT_PROBE_FORMAT,
        help=(
            "framed sends timestamped probe records with seq, send_timestamp_ns, "
            "and payload_size; raw preserves the legacy byte stream "
            f"(default: {DEFAULT_PROBE_FORMAT})"
        ),
    )
    parser.add_argument(
        "--chunk-size",
        type=parse_bytes,
        default=DEFAULT_CHUNK_SIZE,
        help=(
            "Application send chunk size, for example 16KiB "
            f"(default: {DEFAULT_CHUNK_SIZE} bytes)"
        ),
    )
    parser.add_argument(
        "--summary-file",
        default=None,
        help="Write probe summary JSON to this path",
    )
    parser.add_argument(
        "--disable-socket-pacing",
        action="store_true",
        help="Do not set Linux SO_MAX_PACING_RATE on the accepted socket",
    )
    args = parser.parse_args()

    if args.port <= 0:
        parser.error("--port must be positive")
    if args.rate <= 0:
        parser.error("--rate must be positive")
    if args.duration <= 0:
        parser.error("--duration must be positive")
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.probe_format == "framed" and args.chunk_size > 0xFFFFFFFF:
        parser.error("--chunk-size must fit in uint32 for framed probes")

    return args


def main():
    args = parse_args()
    rate_bytes_per_second = args.rate / 8.0
    total_bytes = int(math.ceil(rate_bytes_per_second * args.duration))

    print(
        "Cumulative probe target: "
        f"{total_bytes} bytes at {args.rate / 1_000_000:.3f} Mbit/s "
        f"for {args.duration:.6g}s "
        f"(send_mode={args.send_mode}, probe_format={args.probe_format})"
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((args.host, args.port))
        server_sock.listen(1)
        print(f"Listening on {args.host}:{args.port} ...")

        conn, addr = server_sock.accept()
        with conn:
            print(f"Client connected from {addr}")
            if not args.disable_socket_pacing:
                if set_socket_pacing(conn, rate_bytes_per_second):
                    print(
                        "Set SO_MAX_PACING_RATE to "
                        f"{int(rate_bytes_per_second)} bytes/s "
                        f"({args.rate / 1_000_000:.3f} Mbit/s)"
                    )

            start_wall = time.time()
            if args.probe_format == "framed":
                sent, elapsed, frame_count = send_framed_probe_train(
                    conn=conn,
                    total_payload_bytes=total_bytes,
                    rate_bytes_per_second=rate_bytes_per_second,
                    payload_size=args.chunk_size,
                    send_mode=args.send_mode,
                )
            else:
                frame_count = 0
                if args.send_mode == "paced":
                    sent, elapsed = send_paced(
                        conn=conn,
                        total_bytes=total_bytes,
                        rate_bytes_per_second=rate_bytes_per_second,
                        chunk_size=args.chunk_size,
                    )
                else:
                    sent, elapsed = send_bulk(
                        conn=conn,
                        total_bytes=total_bytes,
                        chunk_size=args.chunk_size,
                    )
                conn.sendall(STOP_COMMAND)
            end_wall = time.time()

    actual_rate_mbit = sent * 8.0 / elapsed / 1_000_000.0 if elapsed > 0 else 0.0
    print(f"Sent {sent} bytes in {elapsed:.6f}s ({actual_rate_mbit:.3f} Mbit/s)")

    write_summary(
        args.summary_file,
        {
            "client_ip": addr[0],
            "client_port": addr[1],
            "server_host": args.host,
            "server_port": args.port,
            "target_rate_mbit_per_second": args.rate / 1_000_000.0,
            "target_rate_bytes_per_second": rate_bytes_per_second,
            "target_duration_seconds": args.duration,
            "target_bytes": total_bytes,
            "send_mode": args.send_mode,
            "probe_format": args.probe_format,
            "timestamp_units": "nanoseconds since Unix epoch in framed headers",
            "probe_frame_count": frame_count,
            "sent_bytes": sent,
            "sent_payload_bytes": sent,
            "elapsed_seconds": elapsed,
            "actual_rate_mbit_per_second": actual_rate_mbit,
            "start_timestamp": start_wall,
            "end_timestamp": end_wall,
            "chunk_size": args.chunk_size,
        },
    )


if __name__ == "__main__":
    main()
