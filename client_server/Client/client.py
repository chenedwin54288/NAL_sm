#!/usr/bin/env python3

import argparse
import socket
import time


CHUNK_SIZE = 1024 * 1024  # 1 MiB
STOP_COMMAND = b"STOP\n"


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
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9000,
        help="Server port (default: 9000)",
    )
    args = parser.parse_args()

    start = time.time()
    with socket.create_connection((args.host, args.port)) as sock:
        received, got_stop = receive_until_stop(sock)

    elapsed = time.time() - start
    mib_per_second = (received / (1024 ** 2)) / elapsed if elapsed > 0 else 0

    print(f"Received {received} bytes in {elapsed:.2f}s ({mib_per_second:.2f} MiB/s)")

    if not got_stop:
        print("Warning: connection closed before STOP signal was received")


if __name__ == "__main__":
    main()
