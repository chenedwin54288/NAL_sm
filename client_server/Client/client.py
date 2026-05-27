#!/usr/bin/env python3

import argparse
import socket
import time


CHUNK_SIZE = 1024 * 1024  # 1 MiB
STOP_COMMAND = b"STOP\n"
DEFAULT_MSS_BYTES = 1460

# TCP_WINDOW_CLAMP limits the maximum receive window this socket advertises to the peer.
# sender cwnd          = congestion-control window, sender-side
# client rwnd          = receive window, advertised by receiver
# TCP_WINDOW_CLAMP     = receiver-side cap on advertised rwnd
# tp->snd_cwnd_clamp   = sender-side cap on sender cwnd
TCP_WINDOW_CLAMP = getattr(socket, "TCP_WINDOW_CLAMP", 10)


def configure_receive_window(sock, rwnd_bytes):
    if rwnd_bytes is None:
        return

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rwnd_bytes)
    sock.setsockopt(socket.IPPROTO_TCP, TCP_WINDOW_CLAMP, rwnd_bytes)


def connect(host, port, rwnd_bytes=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        configure_receive_window(sock, rwnd_bytes)
        sock.connect((host, port))
        return sock
    except Exception:
        sock.close()
        raise


def receive_until_stop(sock):
    received = 0
    pending = b""

    while True:
        data = sock.recv(CHUNK_SIZE)
        if not data:
            received += len(pending)
            return received, False

        pending += data
        stop_index = pending.find(STOP_COMMAND)

        if stop_index != -1:
            payload = pending[:stop_index]
            received += len(payload)
            return received, True

        keep = len(STOP_COMMAND) - 1
        if len(pending) > keep:
            payload = pending[:-keep]
            received += len(payload)
            pending = pending[-keep:]


def main():
    parser = argparse.ArgumentParser(
        description="Receive data from server until the STOP signal is received."
    )
    parser.add_argument(
        "--host",
        default="192.168.88.254",
        help="Server host (default: 192.168.88.254)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9000,
        help="Server port (default: 9000)",
    )
    rwnd_group = parser.add_mutually_exclusive_group()
    rwnd_group.add_argument(
        "--rwnd-bytes",
        type=int,
        default=None,
        help="Advertised receive-window clamp in bytes",
    )
    rwnd_group.add_argument(
        "--rwnd-segments",
        type=int,
        default=None,
        help=(
            "Advertised receive-window clamp in MSS-sized segments "
            f"(default MSS: {DEFAULT_MSS_BYTES} bytes)"
        ),
    )
    parser.add_argument(
        "--mss-bytes",
        type=int,
        default=DEFAULT_MSS_BYTES,
        help=f"MSS bytes used with --rwnd-segments (default: {DEFAULT_MSS_BYTES})",
    )
    args = parser.parse_args()

    if args.rwnd_bytes is not None and args.rwnd_bytes <= 0:
        parser.error("--rwnd-bytes must be positive")
    if args.rwnd_segments is not None and args.rwnd_segments <= 0:
        parser.error("--rwnd-segments must be positive")
    if args.mss_bytes <= 0:
        parser.error("--mss-bytes must be positive")

    rwnd_bytes = args.rwnd_bytes
    if args.rwnd_segments is not None:
        rwnd_bytes = args.rwnd_segments * args.mss_bytes

    start = time.time()
    with connect(args.host, args.port, rwnd_bytes) as sock:
        if rwnd_bytes is not None:
            print(f"Set advertised receive-window clamp to {rwnd_bytes} bytes")
        received, got_stop = receive_until_stop(sock)

    elapsed = time.time() - start
    mib_per_second = (received / (1024 ** 2)) / elapsed if elapsed > 0 else 0

    print(f"Received {received} bytes in {elapsed:.2f}s ({mib_per_second:.2f} MiB/s)")

    if not got_stop:
        print("Warning: connection closed before STOP signal was received")


if __name__ == "__main__":
    main()
