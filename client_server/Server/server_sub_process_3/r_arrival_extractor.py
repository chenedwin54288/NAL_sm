#!/usr/bin/env python3

"""Trace bytes entering Linux TBF and calculate R_arrival samples.

This script uses bpftrace to attach to tbf_enqueue(), which is the enqueue side
of the Linux Token Bucket Filter qdisc. It writes one CSV row per interval:

    timestamp,interval_seconds,bytes,packets,r_arrival_mbit

It is intended to be started by Server/server.py and stopped with SIGTERM.
"""

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_FILE = SCRIPT_DIR / "r_arrival.txt"
DEFAULT_INTERVAL_MS = 1

running = True
bpftrace_process = None


VALUE_PATTERN = re.compile(r"^@(?P<name>bytes|pkts):\s+(?P<value>\d+)\s*$")


def handle_stop(signum, frame):
    global running
    running = False
    stop_bpftrace()


def stop_bpftrace():
    global bpftrace_process

    if bpftrace_process is None or bpftrace_process.poll() is not None:
        return

    try:
        os.killpg(bpftrace_process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        bpftrace_process.terminate()

    try:
        bpftrace_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(bpftrace_process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            bpftrace_process.kill()
        bpftrace_process.wait(timeout=5)


def build_bpftrace_program(interval_ms):
    return f"""
kprobe:tbf_enqueue
{{
  @bytes = sum(((struct sk_buff *)arg0)->len);
  @pkts = count();
}}

interval:ms:{interval_ms}
{{
  print(@bytes);
  print(@pkts);
  clear(@bytes);
  clear(@pkts);
}}
"""


def build_bpftrace_command(program):
    bpftrace_path = shutil.which("bpftrace")
    if bpftrace_path is None:
        raise FileNotFoundError("bpftrace command not found")

    command = [bpftrace_path, "-e", program]
    if os.geteuid() == 0:
        return command

    sudo_path = shutil.which("sudo")
    if sudo_path is None:
        raise FileNotFoundError("sudo command not found")

    return [sudo_path, "-n", *command]


def parse_value(line):
    match = VALUE_PATTERN.match(line.strip())
    if not match:
        return None

    return match.group("name"), int(match.group("value"))


def write_header(output_file, interval_seconds):
    output_file.write("# R_arrival samples from kprobe:tbf_enqueue\n")
    output_file.write(f"# interval_seconds={interval_seconds:.9f}\n")
    output_file.write("timestamp,interval_seconds,bytes,packets,r_arrival_mbit\n")
    output_file.flush()


def append_sample(output_file, interval_seconds, bytes_count, packet_count):
    timestamp = time.time()
    r_arrival_mbit = (bytes_count * 8.0) / interval_seconds / 1_000_000.0
    output_file.write(
        f"{timestamp:.6f},{interval_seconds:.9f},{bytes_count},"
        f"{packet_count},{r_arrival_mbit:.6f}\n"
    )
    output_file.flush()


def append_comment(output_file, message):
    output_file.write(f"# {message}\n")
    output_file.flush()


def run_extractor(output_path, interval_ms):
    global bpftrace_process

    interval_seconds = interval_ms / 1000.0
    program = build_bpftrace_program(interval_ms)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        write_header(output_file, interval_seconds)

        try:
            command = build_bpftrace_command(program)
        except FileNotFoundError as error:
            append_comment(output_file, f"error={error}")
            print(error, file=sys.stderr, flush=True)
            return 1

        try:
            bpftrace_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                start_new_session=True,
            )
        except OSError as error:
            append_comment(output_file, f"error=failed to start bpftrace: {error}")
            print(f"Failed to start bpftrace: {error}", file=sys.stderr, flush=True)
            return 1

        pending_bytes = None
        pending_pkts = None

        assert bpftrace_process.stdout is not None
        while running:
            line = bpftrace_process.stdout.readline()
            if not line:
                if bpftrace_process.poll() is not None:
                    break
                time.sleep(0.01)
                continue

            parsed = parse_value(line)
            if parsed is None:
                stripped = line.strip()
                if stripped:
                    append_comment(output_file, f"bpftrace: {stripped}")
                continue

            name, value = parsed
            if name == "bytes":
                pending_bytes = value
            elif name == "pkts":
                pending_pkts = value

            if pending_bytes is not None and pending_pkts is not None:
                append_sample(output_file, interval_seconds, pending_bytes, pending_pkts)
                pending_bytes = None
                pending_pkts = None

        stop_bpftrace()
        return bpftrace_process.returncode or 0


def main():
    parser = argparse.ArgumentParser(
        description="Trace TBF enqueue bytes and calculate R_arrival_mbit samples."
    )
    parser.add_argument(
        "--output-file",
        default=str(DEFAULT_OUTPUT_FILE),
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_FILE})",
    )
    parser.add_argument(
        "--interval-ms",
        type=int,
        default=DEFAULT_INTERVAL_MS,
        help=f"Sampling interval in milliseconds (default: {DEFAULT_INTERVAL_MS})",
    )
    args = parser.parse_args()

    if args.interval_ms <= 0:
        print("--interval-ms must be greater than 0", file=sys.stderr)
        return 1

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    return run_extractor(Path(args.output_file).resolve(), args.interval_ms)


if __name__ == "__main__":
    raise SystemExit(main())
