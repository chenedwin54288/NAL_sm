#!/usr/bin/env python3

import subprocess
import sys
import time

def run_scripts():
    try:
        # Start backlog_bash.sh in background
        backlog_proc = subprocess.Popen(['./backlog_bash.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Started backlog_bash.sh (PID: {})".format(backlog_proc.pid))

        # Start cwnd_bash.sh in background
        cwnd_proc = subprocess.Popen(['./cwnd_bash.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Started cwnd_bash.sh (PID: {})".format(cwnd_proc.pid))

        print("Both scripts are running. Press Ctrl+C to stop.")

        # Wait for both to finish (they won't, unless interrupted)
        backlog_proc.wait()
        cwnd_proc.wait()

    except KeyboardInterrupt:
        print("\nStopping scripts...")
        backlog_proc.terminate()
        cwnd_proc.terminate()
        backlog_proc.wait()
        cwnd_proc.wait()
        print("Scripts stopped.")
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure the scripts exist and are executable.")
        sys.exit(1)

if __name__ == "__main__":
    run_scripts()