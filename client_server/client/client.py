#!/usr/bin/env python3
import argparse
import socket
import time

ONE_GIB = 1024 ** 3
CHUNK_SIZE = 1024 * 1024  # 1 MiB
cca_name = "my_cca"


def main():
    parser = argparse.ArgumentParser(description="Receive 1 GiB (or custom size) from server.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9000, help="Server port (default: 9000)")
    parser.add_argument("--size", type=int, default=ONE_GIB, help="Bytes to receive (default: 1 GiB)")
    parser.add_argument("--out", default=None, help="Optional output file to write")
    args = parser.parse_args()

    received = 0
    start = time.time()

    out_f = open(args.out, "wb") if args.out else None
    try:
        with socket.create_connection((args.host, args.port)) as s:
            while received < args.size:
                to_read = min(CHUNK_SIZE, args.size - received)
                data = s.recv(to_read)
                if not data:
                    break
                received += len(data)
                if out_f:
                    out_f.write(data)
    finally:
        if out_f:
            out_f.close()

    elapsed = time.time() - start
    mbps = (received / (1024 ** 2)) / elapsed if elapsed > 0 else 0
    print(f"Received {received} bytes in {elapsed:.2f}s ({mbps:.2f} MiB/s)")

    if received < args.size:
        print("Warning: connection closed before expected size was received")


if __name__ == "__main__":
    main()
