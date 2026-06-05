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
import csv
import json
import os
import socket
import struct
import subprocess
import sys
import time

# SERVER and CLIENT commands (can be extended later on)
STOP_COMMAND = b"STOP\n"


SO_MAX_PACING_RATE = getattr(socket, "SO_MAX_PACING_RATE", 47)
DEFAULT_MAX_PACING_RATE_BYTES_PER_SEC = 125_000_000  # 1 Gbit/s
ONE_GIB = (1024 ** 3) * 1 # 1 GiB for better testing of congestion control; adjust as needed
CHUNK_SIZE = 1024 * 1024  # 1 MiB
TCP_INFO = getattr(socket, "TCP_INFO", 11)
TCP_INFO_STRUCT_SIZE = 192
TCP_INFO_SND_SSTHRESH_OFFSET = 76
TCP_INFO_SND_CWND_OFFSET = 80
TCP_INFO_BYTES_ACKED_OFFSET = 120
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_EXTRACTOR_PATH = os.path.join(SCRIPT_DIR, "server_sub_process_1", "log_extractor.py")
R_ARRIVAL_EXTRACTOR_PATH = os.path.join(
    SCRIPT_DIR, "server_sub_process_3", "r_arrival_extractor.py"
)
DEFAULT_R_ARRIVAL_FILE = os.path.join(
    SCRIPT_DIR, "server_sub_process_3", "r_arrival.txt"
)


def mib_per_second(byte_count, elapsed):
    return (byte_count / CHUNK_SIZE) / elapsed if elapsed > 0 else 0


def read_tcp_info(conn):
    try:
        data = conn.getsockopt(socket.IPPROTO_TCP, TCP_INFO, TCP_INFO_STRUCT_SIZE)
    except OSError:
        return None

    if len(data) < TCP_INFO_SND_CWND_OFFSET + 4:
        return None

    info = {
        "snd_ssthresh": struct.unpack_from("=I", data, TCP_INFO_SND_SSTHRESH_OFFSET)[0],
        "snd_cwnd": struct.unpack_from("=I", data, TCP_INFO_SND_CWND_OFFSET)[0],
        "bytes_acked": None,
    }

    if len(data) >= TCP_INFO_BYTES_ACKED_OFFSET + 8:
        info["bytes_acked"] = struct.unpack_from("=Q", data, TCP_INFO_BYTES_ACKED_OFFSET)[0]

    return info


def tcp_info_in_slow_start(tcp_info):
    return tcp_info["snd_cwnd"] < tcp_info["snd_ssthresh"]


def new_slow_start_tracker(conn):
    return {
        "conn": conn,
        "seen_slow_start": False,
        "last_in_slow_start": None,
        "end_time": None,
        "end_bytes_written": None,
        "end_bytes_acked": None,
        "end_snd_cwnd": None,
        "end_snd_ssthresh": None,
    }


def update_slow_start_tracker(tracker, bytes_written):
    if tracker is None or tracker["end_time"] is not None:
        return

    tcp_info = read_tcp_info(tracker["conn"])
    if tcp_info is None:
        return

    in_slow_start = tcp_info_in_slow_start(tcp_info)
    if in_slow_start:
        tracker["seen_slow_start"] = True

    if tracker["last_in_slow_start"] is None:
        tracker["last_in_slow_start"] = in_slow_start
        return

    # previous sample: slow_start
    # current sample: not slow_start
    # at thie moment we write down the INFO
    if tracker["seen_slow_start"] and tracker["last_in_slow_start"] and not in_slow_start:
        tracker["end_time"] = time.time()
        tracker["end_bytes_written"] = bytes_written
        tracker["end_bytes_acked"] = tcp_info["bytes_acked"]
        tracker["end_snd_cwnd"] = tcp_info["snd_cwnd"]
        tracker["end_snd_ssthresh"] = tcp_info["snd_ssthresh"]

    tracker["last_in_slow_start"] = in_slow_start


def summarize_post_slow_start(tracker, total_bytes, start_time, end_time):
    summary = {
        "slow_start_end_time": None,
        "slow_start_end_offset_seconds": None,
        "slow_start_end_bytes_written": None,
        "slow_start_end_bytes_acked": None,
        "slow_start_end_snd_cwnd": None,
        "slow_start_end_snd_ssthresh": None,
        "post_slow_start_elapsed_seconds": None,
        "post_slow_start_bytes": None,
        "post_slow_start_byte_source": None,
        "post_slow_start_mib_per_second": None,
    }

    if tracker is None or tracker["end_time"] is None:
        return summary

    elapsed = end_time - tracker["end_time"]
    final_tcp_info = read_tcp_info(tracker["conn"])
    byte_source = "bytes_written"
    post_slow_start_bytes = total_bytes - tracker["end_bytes_written"]

    if (
        final_tcp_info is not None
        and final_tcp_info["bytes_acked"] is not None
        and tracker["end_bytes_acked"] is not None
    ):
        byte_source = "bytes_acked"
        post_slow_start_bytes = final_tcp_info["bytes_acked"] - tracker["end_bytes_acked"]

    post_slow_start_bytes = max(0, post_slow_start_bytes)

    summary.update(
        {
            "slow_start_end_time": tracker["end_time"],
            "slow_start_end_offset_seconds": tracker["end_time"] - start_time,
            "slow_start_end_bytes_written": tracker["end_bytes_written"],
            "slow_start_end_bytes_acked": tracker["end_bytes_acked"],
            "slow_start_end_snd_cwnd": tracker["end_snd_cwnd"],
            "slow_start_end_snd_ssthresh": tracker["end_snd_ssthresh"],
            "post_slow_start_elapsed_seconds": elapsed,
            "post_slow_start_bytes": post_slow_start_bytes,
            "post_slow_start_byte_source": byte_source,
            "post_slow_start_mib_per_second": mib_per_second(
                post_slow_start_bytes,
                elapsed,
            ),
        }
    )

    return summary


def send_from_file(conn, file_path, size, slow_start_tracker=None):
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
            update_slow_start_tracker(slow_start_tracker, sent)
    return sent


def send_generated(conn, size, slow_start_tracker=None):
    sent = 0
    block = b"\0" * CHUNK_SIZE
    while sent < size:
        to_send = min(CHUNK_SIZE, size - sent)
        conn.sendall(block[:to_send])
        sent += to_send
        update_slow_start_tracker(slow_start_tracker, sent)
    return sent


# Sending this will stop the client.
def send_end_signal(conn):
    conn.sendall(STOP_COMMAND)


def set_max_pacing_rate(sock, bytes_per_second):
    if bytes_per_second <= 0:
        return

    sock.setsockopt(socket.SOL_SOCKET, SO_MAX_PACING_RATE, bytes_per_second)


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


def start_r_arrival_extractor(output_file, interval_ms):
    command = [
        sys.executable,
        R_ARRIVAL_EXTRACTOR_PATH,
        "--output-file",
        output_file,
        "--interval-ms",
        str(interval_ms),
    ]
    return subprocess.Popen(command)


def stop_process(process, process_name):
    if process is None or process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

    print(f"Stopped {process_name}")


def wait_for_file_sample(output_file, timeout=3.0):
    deadline = time.time() + timeout
    path = os.path.abspath(output_file)

    while time.time() < deadline:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as sample_file:
                for line in sample_file:
                    stripped = line.strip()
                    if (
                        stripped
                        and not stripped.startswith("#")
                        and not stripped.startswith("timestamp,")
                    ):
                        return True

        time.sleep(0.05)

    return False


def summarize_r_arrival(output_file, start_timestamp=None, end_timestamp=None):
    path = os.path.abspath(output_file)
    if not os.path.exists(path):
        return {
            "average_r_arrival_mbit": None,
            "max_r_arrival_mbit": None,
            "r_arrival_sample_count": 0,
        }

    samples = []
    total_bytes = 0
    total_interval_seconds = 0.0
    with open(path, "r", encoding="utf-8", newline="") as arrival_file:
        csv_lines = (
            line for line in arrival_file if line.strip() and not line.startswith("#")
        )
        reader = csv.DictReader(csv_lines)
        for row in reader:
            try:
                timestamp = float(row.get("timestamp", ""))
            except ValueError:
                continue

            if start_timestamp is not None and timestamp < start_timestamp:
                continue

            if end_timestamp is not None and timestamp > end_timestamp:
                continue

            value = row.get("r_arrival_mbit")
            if not value:
                continue
            try:
                interval_seconds = float(row.get("interval_seconds", ""))
                bytes_count = int(row.get("bytes", ""))
                r_arrival_mbit = float(value)
            except ValueError:
                continue

            samples.append(r_arrival_mbit)
            total_bytes += bytes_count
            total_interval_seconds += interval_seconds

    if not samples:
        return {
            "average_r_arrival_mbit": None,
            "max_r_arrival_mbit": None,
            "r_arrival_sample_count": 0,
        }

    average_r_arrival_mbit = None
    if total_interval_seconds > 0:
        average_r_arrival_mbit = (
            total_bytes * 8.0 / total_interval_seconds / 1_000_000.0
        )

    return {
        "average_r_arrival_mbit": average_r_arrival_mbit,
        "max_r_arrival_mbit": max(samples),
        "r_arrival_sample_count": len(samples),
    }


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
    parser.add_argument("--r-arrival-extractor", action="store_true", help="Run the TBF enqueue-rate extractor during the transfer")
    parser.add_argument("--r-arrival-output-file", default=DEFAULT_R_ARRIVAL_FILE, help="Output file for R_arrival samples")
    parser.add_argument("--r-arrival-interval-ms", type=int, default=1, help="Milliseconds between R_arrival samples (default: 1)")
    parser.add_argument("--summary-file", default=None, help="Write transfer summary JSON to this path")
    parser.add_argument(
        "--max-pacing-rate",
        type=int,
        default=DEFAULT_MAX_PACING_RATE_BYTES_PER_SEC,
        help=(
            "Linux SO_MAX_PACING_RATE in bytes/s for the accepted TCP socket "
            "(default: 125000000, i.e. 1 Gbit/s; set 0 to disable)"
        ),
    )
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
    r_arrival_process = None
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
                set_max_pacing_rate(conn, args.max_pacing_rate)
                if args.max_pacing_rate > 0:
                    print(
                        "Set SO_MAX_PACING_RATE to "
                        f"{args.max_pacing_rate} bytes/s "
                        f"({args.max_pacing_rate * 8 / 1_000_000:.2f} Mbit/s)"
                    )

                if args.r_arrival_extractor:
                    r_arrival_process = start_r_arrival_extractor(
                        args.r_arrival_output_file,
                        args.r_arrival_interval_ms,
                    )
                    print(f"Started R_arrival extractor with PID {r_arrival_process.pid}")
                    if not wait_for_file_sample(args.r_arrival_output_file):
                        print(
                            "Warning: R_arrival extractor did not produce a sample before transfer start",
                            file=sys.stderr,
                        )

                slow_start_tracker = new_slow_start_tracker(conn)
                update_slow_start_tracker(slow_start_tracker, 0)
                start = time.time()
                if file_path:
                    total = send_from_file(conn, file_path, args_size, slow_start_tracker)
                else:
                    total = send_generated(conn, args_size, slow_start_tracker)
                
                # STOP COMMAND to inform the client to terminate the connection
                send_end_signal(conn)
                end = time.time()
                elapsed = end - start

                mbps = mib_per_second(total, elapsed)
                print(f"Sent {total} bytes in {elapsed:.2f}s ({mbps:.2f} MiB/s)")
                post_slow_start_summary = summarize_post_slow_start(
                    slow_start_tracker,
                    total,
                    start,
                    end,
                )
                if post_slow_start_summary["post_slow_start_mib_per_second"] is None:
                    print("Slow start end was not detected during this transfer")
                else:
                    print(
                        "After slow start: "
                        f"{post_slow_start_summary['post_slow_start_mib_per_second']:.2f} MiB/s "
                        f"over {post_slow_start_summary['post_slow_start_elapsed_seconds']:.2f}s "
                        f"({post_slow_start_summary['post_slow_start_byte_source']})"
                    )

                r_arrival_summary = {
                    "average_r_arrival_mbit": None,
                    "max_r_arrival_mbit": None,
                    "r_arrival_sample_count": 0,
                }
                if r_arrival_process is not None:
                    stop_process(r_arrival_process, "R_arrival extractor")
                    r_arrival_process = None
                    r_arrival_summary = summarize_r_arrival(args.r_arrival_output_file)

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
                        "max_pacing_rate_bytes_per_second": args.max_pacing_rate,
                        **post_slow_start_summary,
                        **r_arrival_summary,
                    }
                    os.makedirs(os.path.dirname(os.path.abspath(args.summary_file)), exist_ok=True)
                    with open(args.summary_file, "w", encoding="utf-8") as summary_file:
                        json.dump(summary, summary_file, indent=2)
                        summary_file.write("\n")
    finally:
        if r_arrival_process is not None:
            stop_process(r_arrival_process, "R_arrival extractor")
        if log_process is not None:
            stop_process(log_process, "log extractor")


if __name__ == "__main__":
    main()
