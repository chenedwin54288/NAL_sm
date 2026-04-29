#!/usr/bin/env python3

# Example command:
#     python3 Server/server.py \
#       --host 0.0.0.0 \
#       --port 9000 \
#       --size 1 \
#       --file client_server/1GB.zip
#       --cca my_cca
#     
#     python3 Server/server.py --cca reno --log-extractor
#
#     python3 client_server/Server/server.py \
#       --cca my_cca \
#       --log-extractor \
#       --log-interval 0.5


# - start a subprocess that runs log_extractor&cleaner to extract && clean the kernel ring in certain intervals
# - new connection from a client, start a timer
# - send the data to the client (this data can be from a file or blocks of 0s)
# - at the end, send a STOP COMMAND to the client and stop the log_extractor&cleaner

import argparse
import json
import os
import socket
import subprocess
import sys
import time

# SERVER and CLIENT commands (can be extended later on)
STOP_COMMAND = b"STOP\n"


ONE_GIB = (1024 ** 3) * 1 # 1 GiB for better testing of congestion control; adjust as needed
CHUNK_SIZE = 1024 * 1024  # 1 MiB
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_EXTRACTOR_PATH = os.path.join(SCRIPT_DIR, "server_sub_process_1", "log_extractor.py")


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


# Sending this will stop the client.
def send_end_signal(conn):
    conn.sendall(STOP_COMMAND)


def start_log_extractor(context_file, interval):
    command = [
        sys.executable,
        LOG_EXTRACTOR_PATH,
        "--context-file",
        context_file,
        "--interval",
        str(interval),
    ]
    return subprocess.Popen(command)


def main():
    parser = argparse.ArgumentParser(description="Send data to a single client.")
    parser.add_argument("--host", default="192.168.88.254", help="Bind host (default: 192.168.88.254)")
    parser.add_argument("--port", type=int, default=9000, help="Bind port (default: 9000)")
    parser.add_argument("--size", type=int, default=1, help="GiB to send (default: 1)")
    parser.add_argument("--file", default=None, help="File to stream (defaults to ../1GB.zip if present)")
    parser.add_argument("--cca", default="reno", help="Select the congestion control algorithm to use (default: reno)")

    parser.add_argument("--log-extractor", action="store_true", help="Run the kernel log extractor during the transfer")
    parser.add_argument("--log-context-file", default=os.path.join(SCRIPT_DIR, "server_sub_process_1", "context.txt"), help="Output file for extracted kernel logs")
    parser.add_argument("--log-interval", type=float, default=0.5, help="Seconds between log extractions (default: 0.5)")
    parser.add_argument("--summary-file", default=None, help="Write transfer summary JSON to this path")
    args = parser.parse_args()

    file_path = args.file
    args_size = args.size * ONE_GIB
    if file_path:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise SystemExit(f"File is empty: {file_path}")
        if file_size < args_size:
            print(f"Note: file smaller than size; will loop file to reach {args_size} GB")
        else:
            print(f"Streaming first {args_size} GB from file: {file_path}")
    else:
        print(f"Generating {args_size} GB of zeros")


    log_process = None
    try:
        # start the log_extractor && log_cleaner
        if args.log_extractor:
            log_process = start_log_extractor(args.log_context_file, args.log_interval)
            print(f"Started log extractor with PID {log_process.pid}")
        
        # open a socket and start listening
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            
            cca_name = args.cca.encode("ascii")
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
                    total = send_from_file(conn, file_path, args_size)
                else:
                    total = send_generated(conn, args_size)
                
                # STOP COMMAND to inform the client to terminate the connection
                send_end_signal(conn)
                elapsed = time.time() - start

                mbps = (total / (CHUNK_SIZE)) / elapsed if elapsed > 0 else 0
                print(f"Sent {total} bytes in {elapsed:.2f}s ({mbps:.2f} MiB/s)")

                # Summarize the session information as a JSON 
                # run.sh will pass it to AnalysisPhase
                if args.summary_file:
                    summary = {
                        "cca": args.cca,
                        "client_ip": addr[0],
                        "client_port": addr[1],
                        "elapsed_seconds": elapsed,
                        "mib_per_second": mbps,
                        "server_host": args.host,
                        "server_port": args.port,
                        "size_gib": args.size,
                        "total_bytes": total,
                    }
                    os.makedirs(os.path.dirname(os.path.abspath(args.summary_file)), exist_ok=True)
                    with open(args.summary_file, "w", encoding="utf-8") as summary_file:
                        json.dump(summary, summary_file, indent=2)
                        summary_file.write("\n")
    finally:
        if log_process is not None:
            log_process.terminate()
            log_process.wait()
            print("Stopped log extractor")


if __name__ == "__main__":
    main()
