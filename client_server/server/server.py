#!/usr/bin/env python3
import argparse
import os
import socket
import time

ONE_GIB = (1024 ** 3) * 10 # 1 GiB for better testing of congestion control; adjust as needed
CHUNK_SIZE = 1024 * 1024  # 1 MiB
cca_name = b"my_cca"


def send_from_file(conn, file_path, size):
    sent = 0
    with open(file_path, "rb") as f:
        while sent < size:
            to_read = min(CHUNK_SIZE, size - sent)
            data = f.read(to_read)
            if not data:
                # EOF reached early; restart file
                f.seek(0)
                continue
            conn.sendall(data)
            sent += len(data)
    return sent


def send_generated(conn, size):
    sent = 0
    block = b"\0" * CHUNK_SIZE
    while sent < size:
        to_send = min(CHUNK_SIZE, size - sent)
        conn.sendall(block[:to_send])
        sent += to_send
    return sent


def main():
    parser = argparse.ArgumentParser(description="Send 1 GiB (or custom size) to a single client.")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="Bind port (default: 9000)")
    parser.add_argument("--size", type=int, default=ONE_GIB, help="Bytes to send (default: 1 GiB)")
    parser.add_argument("--file", default=None, help="File to stream (defaults to ../1GB.zip if present)")
    args = parser.parse_args()

    file_path = args.file
    if file_path is None:
        candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "1GB.zip"))
        if os.path.isfile(candidate):
            file_path = candidate

    if file_path:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise SystemExit(f"File is empty: {file_path}")
        if file_size < args.size:
            print(f"Note: file smaller than size; will loop file to reach {args.size} bytes")
        else:
            print(f"Streaming first {args.size} bytes from file: {file_path}")
    else:
        print(f"Generating {args.size} bytes of zeros")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, cca_name)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.host, args.port))
        s.listen(1)
        print(f"Listening on {args.host}:{args.port} ...")
        conn, addr = s.accept()
        with conn:
            print(f"Client connected from {addr}")
            start = time.time()
            if file_path:
                total = send_from_file(conn, file_path, args.size)
            else:
                total = send_generated(conn, args.size)
            elapsed = time.time() - start
            mbps = (total / (1024 ** 2)) / elapsed if elapsed > 0 else 0
            print(f"Sent {total} bytes in {elapsed:.2f}s ({mbps:.2f} MiB/s)")


if __name__ == "__main__":
    main()
