#!/usr/bin/env python3

# This script repeatedly extracts the kernel ring buffer and appends it to context.txt, then clears the ring buffer.
# It runs until it receives a SIGTERM or SIGINT signal.
# Example command:
#    python3 log_extractor.py --context-file /path/to/context.txt --interval 1.0


import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONTEXT_FILE = SCRIPT_DIR / "context.txt"
running = True


def handle_stop(signum, frame):
    global running
    running = False


def run_command(command):
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def should_retry_with_sudo(stderr):
    return "Operation not permitted" in stderr or "Permission denied" in stderr


def run_dmesg_command(*args):
    result = run_command(["dmesg", *args])
    if result.returncode == 0 or not should_retry_with_sudo(result.stderr):
        return result

    return run_command(["sudo", "-n", "dmesg", *args])


def append_kernel_log(context_file):
    result = run_dmesg_command()

    if result.returncode != 0:
        print(
            f"Failed to read kernel ring buffer: {result.stderr.strip()}",
            file=sys.stderr,
            flush=True,
        )
        return False

    if result.stdout:
        with context_file.open("a", encoding="utf-8") as f:
            f.write(result.stdout)
            if not result.stdout.endswith("\n"):
                f.write("\n")

    return True


def clear_kernel_log():
    result = run_dmesg_command("--clear")

    if result.returncode != 0:
        print(
            f"Failed to clear kernel ring buffer: {result.stderr.strip()}",
            file=sys.stderr,
            flush=True,
        )
        return False

    return True


def clean_context_file(context_file):
    context_file.write_text("", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Repeatedly copy the kernel ring buffer to context.txt, then clear it."
    )
    parser.add_argument(
        "--context-file",
        default=str(DEFAULT_CONTEXT_FILE),
        help=f"Output file for extracted logs (default: {DEFAULT_CONTEXT_FILE})",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Seconds to sleep between extractions (default: 0.5)",
    )
    args = parser.parse_args()

    context_file = Path(args.context_file).resolve()
    context_file.parent.mkdir(parents=True, exist_ok=True)
    clean_context_file(context_file)

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    while running:
        if append_kernel_log(context_file):
            clear_kernel_log()

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
