#!/usr/bin/env python3

import subprocess
import sys
import time

def run_scripts():

    # clean up any existing log files
    files_to_clear = ['backlog.txt', 'cwnd_log.txt']
    for filename in files_to_clear:
        with open(filename, 'w') as f:
            pass

    try:
        # Start track_backlog.sh in background
        backlog_proc = subprocess.Popen(['./track_backlog.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Started track_backlog.sh (PID: {})".format(backlog_proc.pid))

        # Start track_cwnd.sh in background
        cwnd_proc = subprocess.Popen(['./track_cwnd.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Started track_cwnd.sh (PID: {})".format(cwnd_proc.pid))

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