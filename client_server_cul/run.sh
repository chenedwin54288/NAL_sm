#!/usr/bin/env bash

# Example command:  
#    ./client_server/run.sh \
#      --cca my_cca \
#      --size-gib 3 \
#      --rtt-ms 20 \
#      --rate-mbit 100 \
#      --tbf-rate 100mbit \
#      --tbf-burst 32kbit \
#      --tbf-limit 10000

# ./run.sh --cca my_cca --size-gib 3 --rtt-ms 400 --rate-mbit 1000 --tbf-rate 1Gbit --tbf-burst 1mb --tbf-limit 50000 


# Stop immediately on errors, unset variables, and failed pipeline commands.
set -euo pipefail

# Keep a copy of the terminal mode so background tools cannot leave the shell
# with broken newline/cursor behavior after this script exits.
ORIGINAL_STTY="$(stty -g 2>/dev/null || true)"
restore_tty() {
  if [[ -n "${ORIGINAL_STTY:-}" ]]; then
    stty "$ORIGINAL_STTY" 2>/dev/null || true
  fi
}

CUMULATIVE_PID=""
stop_cumulative_server() {
  if [[ -n "${CUMULATIVE_PID:-}" ]] && kill -0 "$CUMULATIVE_PID" 2>/dev/null; then
    printf '\n==> Stopping cumulative probe server\n'
    kill "$CUMULATIVE_PID" 2>/dev/null || true
    wait "$CUMULATIVE_PID" 2>/dev/null || true
  fi
}
finish_cumulative_server() {
  if [[ -z "${CUMULATIVE_PID:-}" ]]; then
    return
  fi

  if [[ -n "${TMP_CUMULATIVE_SUMMARY:-}" && -f "$TMP_CUMULATIVE_SUMMARY" ]]; then
    wait "$CUMULATIVE_PID" 2>/dev/null || true
  else
    stop_cumulative_server
  fi
  CUMULATIVE_PID=""
}
cleanup() {
  stop_cumulative_server
  restore_tty
}
trap cleanup EXIT
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

# Resolve all project paths relative to this script, so it can be run from any directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_PATH="$SCRIPT_DIR/Server/server.py"
CUMULATIVE_SERVER_PATH="$SCRIPT_DIR/Server/server_cumulative.py"
INIT_CCA_PATH="$SCRIPT_DIR/custom_cca/init_cca.sh"
FILTER_IP_PATH="$SCRIPT_DIR/AnalysisPhase/filter_ip.py"
EXTRACT_IP_INFO_PATH="$SCRIPT_DIR/AnalysisPhase/extract_ip_info.py"
EXTRACT_IP_CWND_PATH="$SCRIPT_DIR/AnalysisPhase/extract_ip_cwnd.py"
DB_DIR="$SCRIPT_DIR/DB"

# Default experiment parameters. Each one can be overridden with CLI options below.
DEV="eno1"
CCA="my_cca"
DATA_SIZE_GIB="1"
SERVER_HOST="0.0.0.0"
SERVER_PORT="9000"
CUMULATIVE_ENABLED="1"
CUMULATIVE_PORT="9001"
CUMULATIVE_RATE=""
CUMULATIVE_DURATION="1.2"
CUMULATIVE_CHUNK_SIZE=""
CUMULATIVE_SEND_MODE=""
LOG_INTERVAL="0.5"
MSS_BYTES="1460"
RTT_MS=""
RATE_MBIT=""
TBF_RATE=""
TBF_BURST=""
TBF_LIMIT=""
CWND=""
FILE_PATH=""

DATA_START=1
DATA_END=500

# Print the supported command line options.
usage() {
  cat <<USAGE
Usage:
  $0 [options]

Options:
  --cca NAME              TCP congestion control algorithm (default: my_cca)
  --size-gib N            Data size to send in GiB (default: 1)
  --host HOST             Server bind host (default: 0.0.0.0)
  --port PORT             Server bind port (default: 9000)
  --dev IFACE             Network interface for TBF reset/config (default: eno1)
  --file PATH             File to stream instead of generated zero bytes
  --log-interval SECONDS  Kernel log extraction interval (default: 0.5)

  --cumulative-port N         Cumulative probe server port (default: 9001)
  --cumulative-rate RATE      Override cumulative probe send rate
  --cumulative-duration SEC   Override cumulative probe duration
  --cumulative-chunk-size N   Override cumulative probe send chunk size
  --cumulative-send-mode M    Cumulative probe send mode: paced or bulk
  --no-cumulative             Do not start the cumulative probe server

  --cwnd N                Use this CWND limit directly for my_cca; 0 disables the cap
  --rtt-ms N              RTT in milliseconds, used to calculate CWND
  --rate-mbit N           Rate in Mbit/s, used to calculate CWND
  --mss-bytes N           MSS in bytes for CWND calculation (default: 1460)

  --tbf-rate RATE         tc TBF rate, for example 100mbit
  --tbf-burst BURST       tc TBF burst, for example 32kbit
  --tbf-limit LIMIT       tc TBF limit, for example 10000

Example:
  $0 --cca my_cca --size-gib 3 --cwnd 80
  $0 --cca my_cca --size-gib 3 --rtt-ms 20 --rate-mbit 100 --tbf-rate 100mbit --tbf-burst 32kbit --tbf-limit 10000
  $0 --cca reno --size-gib 1
USAGE
}

# Print a visible progress message.
log() {
  printf '\n==> %s\n' "$*"
}

# Print an error and stop the script.
die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

# Require a command before the experiment starts, so failures are early and clear.
need_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

# Small validators for integer options.
is_positive_int() {
  [[ "$1" =~ ^[0-9]+$ ]] && (( "$1" > 0 ))
}

is_nonnegative_int() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

# Calculate CWND from bandwidth-delay product:
#   cwnd = ceil(max(rtt * rate + tbf_limit - mss, mss) / mss)
# RTT is given in ms, rate in Mbit/s, and the result is in MSS-sized segments.
calculate_cwnd() {
  python3 - "$RTT_MS" "$RATE_MBIT" "$TBF_LIMIT" "$MSS_BYTES" <<'PY'
import math
import sys

rtt_ms = float(sys.argv[1])
rate_mbit = float(sys.argv[2])
limit_bytes = int(sys.argv[3] or 0)
mss_bytes = int(sys.argv[4])

bdp_bytes = (rtt_ms / 1000.0) * (rate_mbit * 1_000_000.0 / 8.0)
cwnd = math.ceil(max(bdp_bytes + limit_bytes - mss_bytes, mss_bytes) / mss_bytes)
print(cwnd)
PY
}

# Read a simple top-level field from a JSON file.
# Used after server.py writes the transfer summary.
json_field() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

value = data.get(sys.argv[2], "")
print(value)
PY
}

# Print final experiment metrics gathered from the run artifacts.
print_final_metrics() {
  python3 - "$1" "$2" "$3" <<'PY'
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
ip_info_path = Path(sys.argv[2])
server_log_path = Path(sys.argv[3])


def read_json(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def fmt_float(value, digits=6):
    if value is None or value == "":
        return "N/A"
    return f"{float(value):.{digits}f}"


summary = read_json(summary_path)
ip_info = read_json(ip_info_path)

row_count = ip_info.get("row_count")
phase_counts = ip_info.get("phase_counts", {})
loss_recovery = phase_counts.get("loss_recovery")
fast_retransmit = phase_counts.get("fast_retransmit")
drop_rate = None
drop_rate_with_fast_retransmit = None
if row_count:
    drop_rate = (loss_recovery or 0) / row_count
    drop_rate_with_fast_retransmit = (
        (loss_recovery or 0) + (fast_retransmit or 0)
    ) / row_count

post_mib = summary.get("post_slow_start_mib_per_second")
post_mbit = summary.get("post_slow_start_mbit_per_second")
post_bytes = summary.get("post_slow_start_bytes")
post_elapsed = summary.get("post_slow_start_elapsed_seconds")
if post_mbit is None and post_bytes is not None and post_elapsed:
    post_mbit = post_bytes * 8.0 / post_elapsed / 1_000_000.0

after_slow_start_line = ""
if server_log_path.exists():
    with server_log_path.open("r", encoding="utf-8") as log_file:
        for line in log_file:
            if "After slow start:" in line:
                after_slow_start_line = line.strip()

print(f"Drop rate: {fmt_float(drop_rate)}", end="")
if row_count:
    print(f" ({loss_recovery or 0}/{row_count} loss_recovery rows)")
else:
    print(" (N/A)")
print(
    "Drop rate incl. fast retransmit: "
    f"{fmt_float(drop_rate_with_fast_retransmit)}",
    end="",
)
if row_count:
    print(
        " ("
        f"{(loss_recovery or 0) + (fast_retransmit or 0)}/{row_count} "
        f"loss_recovery + fast_retransmit rows"
        ")"
    )
else:
    print(" (N/A)")
print(f"post_slow_start_mbit_per_second: {fmt_float(post_mbit)}")
print(f"post_slow_start_mib_per_second: {fmt_float(post_mib)}")
print(
    "Server after slow start: "
    f"{after_slow_start_line if after_slow_start_line else 'N/A'}"
)
PY
}

# Parse command line arguments. Most options directly override the defaults above.
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cca)
      CCA="${2:-}"; shift 2 ;;
    --size-gib)
      DATA_SIZE_GIB="${2:-}"; shift 2 ;;
    --host)
      SERVER_HOST="${2:-}"; shift 2 ;;
    --port)
      SERVER_PORT="${2:-}"; shift 2 ;;
    --cumulative-port)
      CUMULATIVE_PORT="${2:-}"; shift 2 ;;
    --cumulative-rate)
      CUMULATIVE_RATE="${2:-}"; shift 2 ;;
    --cumulative-duration)
      CUMULATIVE_DURATION="${2:-}"; shift 2 ;;
    --cumulative-chunk-size)
      CUMULATIVE_CHUNK_SIZE="${2:-}"; shift 2 ;;
    --cumulative-send-mode)
      CUMULATIVE_SEND_MODE="${2:-}"; shift 2 ;;
    --no-cumulative)
      CUMULATIVE_ENABLED="0"; shift ;;
    --dev)
      DEV="${2:-}"; shift 2 ;;
    --file)
      FILE_PATH="${2:-}"; shift 2 ;;
    --log-interval)
      LOG_INTERVAL="${2:-}"; shift 2 ;;
    --cwnd)
      CWND="${2:-}"; shift 2 ;;
    --rtt-ms)
      RTT_MS="${2:-}"; shift 2 ;;
    --rate-mbit)
      RATE_MBIT="${2:-}"; shift 2 ;;
    --mss-bytes)
      MSS_BYTES="${2:-}"; shift 2 ;;
    --tbf-rate)
      TBF_RATE="${2:-}"; shift 2 ;;
    --tbf-burst)
      TBF_BURST="${2:-}"; shift 2 ;;
    --tbf-limit)
      TBF_LIMIT="${2:-}"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      die "unknown option: $1" ;;
  esac
done











# Check required tools and project files before changing tc/module/server state.
need_command python3
need_command sudo
need_command tc

[[ -f "$SERVER_PATH" ]] || die "server not found: $SERVER_PATH"
[[ -f "$CUMULATIVE_SERVER_PATH" ]] || die "cumulative server not found: $CUMULATIVE_SERVER_PATH"
[[ -f "$FILTER_IP_PATH" ]] || die "filter_ip.py not found"
[[ -f "$EXTRACT_IP_INFO_PATH" ]] || die "extract_ip_info.py not found"
[[ -f "$EXTRACT_IP_CWND_PATH" ]] || die "extract_ip_cwnd.py not found"

is_positive_int "$DATA_SIZE_GIB" || die "--size-gib must be a positive integer"
is_positive_int "$SERVER_PORT" || die "--port must be a positive integer"
is_positive_int "$CUMULATIVE_PORT" || die "--cumulative-port must be a positive integer"
is_positive_int "$MSS_BYTES" || die "--mss-bytes must be a positive integer"

if [[ "$CUMULATIVE_ENABLED" == "1" && "$CUMULATIVE_PORT" == "$SERVER_PORT" ]]; then
  die "--cumulative-port must differ from --port"
fi

# If a file is provided, server.py streams it repeatedly until --size-gib is reached.
if [[ -n "$FILE_PATH" && ! -f "$FILE_PATH" ]]; then
  die "--file does not exist: $FILE_PATH"
fi

# my_cca needs a CWND limit. It can be passed directly or calculated from RTT/rate.
if [[ -n "$CWND" ]]; then
  is_nonnegative_int "$CWND" || die "--cwnd must be a non-negative integer"
elif [[ "$CCA" == "my_cca" ]]; then
  [[ -n "$RTT_MS" ]] || die "my_cca needs --cwnd or --rtt-ms with --rate-mbit"
  [[ -n "$RATE_MBIT" ]] || die "my_cca needs --cwnd or --rtt-ms with --rate-mbit"
  CWND="$(calculate_cwnd)"
fi

# TBF parameters must be complete because tc needs all three values together.
if [[ -n "$TBF_RATE$TBF_BURST$TBF_LIMIT" ]]; then
  [[ -n "$TBF_RATE" && -n "$TBF_BURST" && -n "$TBF_LIMIT" ]] || \
    die "set --tbf-rate, --tbf-burst, and --tbf-limit together"
fi

# Use a temporary DB directory while the server is running. After the run, files are
# moved into the final directory once we know the real client port.
RUN_ID="$(date +%Y%m%d_%H%M%S)"
TMP_DIR="$DB_DIR/.tmp_$RUN_ID"
TMP_CONTEXT="$TMP_DIR/context.txt"
TMP_R_ARRIVAL="$TMP_DIR/r_arrival.txt"
TMP_SUMMARY="$TMP_DIR/transfer_summary.json"
TMP_SERVER_LOG="$TMP_DIR/server.log"
TMP_CUMULATIVE_SUMMARY="$TMP_DIR/cumulative_server_summary.json"
TMP_CUMULATIVE_LOG="$TMP_DIR/cumulative_server.log"
mkdir -p "$TMP_DIR"















# Remove any existing root qdisc so every experiment starts from a known state.
log "Resetting TBF on $DEV"
sudo tc qdisc del dev "$DEV" root 2>/dev/null || true


# Optionally apply a new Token Bucket Filter for this experiment.
if [[ -n "$TBF_RATE" ]]; then
  log "Applying TBF: rate=$TBF_RATE burst=$TBF_BURST limit=$TBF_LIMIT"
  sudo tc qdisc add dev "$DEV" root tbf rate "$TBF_RATE" burst "$TBF_BURST" limit "$TBF_LIMIT"
  sudo ethtool -K eno1 tso off
  sudo ethtool -K eno1 gso off
  
  

  # # 1. Add the TBF qdisc as the root
  # sudo tc qdisc add dev "$DEV" root handle 1: tbf \
  #     rate "$TBF_RATE" \
  #     burst "$TBF_BURST" \
  #     limit "$TBF_LIMIT"

  # # 2. Add the 1ms delay as a child of the TBF qdisc
  # sudo tc qdisc add dev "$DEV" parent 1: handle 10: netem delay 1ms limit 1000

  # # 1. Root netem with a custom queue size (4p = 5840)
  # sudo tc qdisc add dev "$DEV" root handle 1: netem delay 1ms limit 4

  # # 2. Child TBF (this has its own 'limit' for rate-limiting)
  # sudo tc qdisc add dev "$DEV" parent 1: handle 10: tbf \
  #     rate "$TBF_RATE" \
  #     burst "$TBF_BURST" \
  #     limit 1480b
fi

# Load my_cca with the chosen CWND limit. Other CCAs are selected inside server.py.
if [[ "$CCA" == "my_cca" ]]; then
  if [[ "$CWND" == "0" ]]; then
    log "Initializing my_cca with CWND limit disabled"
  else
    log "Initializing my_cca with CWND limit $CWND"
  fi
  "$INIT_CCA_PATH" "$CWND"
else
  log "Using kernel CCA $CCA"
fi

# log_extractor.py may need sudo for dmesg on systems with kernel.dmesg_restrict=1.
# r_arrival_extractor.py may need sudo for bpftrace.
# Refresh sudo now so non-interactive sudo calls can work while the server runs.
log "Refreshing sudo access for background extractors"
sudo -v

if [[ "$CUMULATIVE_ENABLED" == "1" ]]; then
  CUMULATIVE_CMD=(
    python3 -u "$CUMULATIVE_SERVER_PATH"
    --host "$SERVER_HOST"
    --port "$CUMULATIVE_PORT"
    --summary-file "$TMP_CUMULATIVE_SUMMARY"
  )

  if [[ -n "$CUMULATIVE_RATE" ]]; then
    CUMULATIVE_CMD+=(--rate "$CUMULATIVE_RATE")
  fi
  if [[ -n "$CUMULATIVE_DURATION" ]]; then
    CUMULATIVE_CMD+=(--duration "$CUMULATIVE_DURATION")
  fi
  if [[ -n "$CUMULATIVE_CHUNK_SIZE" ]]; then
    CUMULATIVE_CMD+=(--chunk-size "$CUMULATIVE_CHUNK_SIZE")
  fi
  if [[ -n "$CUMULATIVE_SEND_MODE" ]]; then
    CUMULATIVE_CMD+=(--send-mode "$CUMULATIVE_SEND_MODE")
  fi

  log "Starting cumulative probe server on $SERVER_HOST:$CUMULATIVE_PORT"
  "${CUMULATIVE_CMD[@]}" >"$TMP_CUMULATIVE_LOG" 2>&1 &
  CUMULATIVE_PID="$!"
  sleep 0.2
  if ! kill -0 "$CUMULATIVE_PID" 2>/dev/null; then
    sed -n '1,120p' "$TMP_CUMULATIVE_LOG" >&2 || true
    die "cumulative probe server failed to start"
  fi
  log "Cumulative probe server ready. Tester should run client_cumulative first."
fi

# Build the server command as an array so paths and values with spaces stay safe.
SERVER_CMD=(
  sudo -E python3 "$SERVER_PATH"
  --host "$SERVER_HOST"
  --port "$SERVER_PORT"
  --size "$DATA_SIZE_GIB"
  --cca "$CCA"
  --log-extractor
  --log-context-file "$TMP_CONTEXT"
  --log-interval "$LOG_INTERVAL"
  --r-arrival-extractor
  --r-arrival-output-file "$TMP_R_ARRIVAL"
  --summary-file "$TMP_SUMMARY"
)

if [[ -n "$FILE_PATH" ]]; then
  SERVER_CMD+=(--file "$FILE_PATH")
fi

# This blocks until one client connects, receives all data, and the server exits.
log "Starting normal server. After the cumulative probe, connect to $SERVER_HOST:$SERVER_PORT"
"${SERVER_CMD[@]}" 2>&1 | tee "$TMP_SERVER_LOG"
finish_cumulative_server

[[ -f "$TMP_SUMMARY" ]] || die "server did not write summary file: $TMP_SUMMARY"

# server.py records the client IP, ephemeral port, and elapsed transfer time here.
CLIENT_IP="$(json_field "$TMP_SUMMARY" client_ip)"
CLIENT_PORT="$(json_field "$TMP_SUMMARY" client_port)"
ELAPSED_SECONDS="$(json_field "$TMP_SUMMARY" elapsed_seconds)"
DATA_LABEL="${DATA_SIZE_GIB}GB"
CWND_LABEL="${CWND:-none}"
if [[ "$CCA" == "my_cca" ]]; then
  OUTPUT_DIR="$DB_DIR/$DATA_LABEL/${DATA_LABEL}_${CLIENT_PORT}_${CWND_LABEL}"
else
  OUTPUT_DIR="$DB_DIR/$DATA_LABEL/${DATA_LABEL}_${CLIENT_PORT}_${CCA}"
fi
FILTERED_CSV="$OUTPUT_DIR/filtered_context.csv"
INFO_JSON="$OUTPUT_DIR/ip_info.json"
CWND_PNG="$OUTPUT_DIR/cwnd_${CLIENT_IP//./_}_${CLIENT_PORT}.png"




# BELOW will only be ran if my cca selection=="my_cca"
# Save raw logs and metadata in the final DB location:
#   DB/<size>/<size>_<client-port>_<cwnd>/
log "Creating output directory $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
mv "$TMP_SUMMARY" "$OUTPUT_DIR/transfer_summary.json"
mv "$TMP_SERVER_LOG" "$OUTPUT_DIR/server.log"
if [[ -f "$TMP_CUMULATIVE_SUMMARY" ]]; then
  mv "$TMP_CUMULATIVE_SUMMARY" "$OUTPUT_DIR/cumulative_server_summary.json"
fi
if [[ -f "$TMP_CUMULATIVE_LOG" ]]; then
  mv "$TMP_CUMULATIVE_LOG" "$OUTPUT_DIR/cumulative_server.log"
fi
if [[ -f "$TMP_R_ARRIVAL" ]]; then
  mv "$TMP_R_ARRIVAL" "$OUTPUT_DIR/r_arrival.txt"
else
  : > "$OUTPUT_DIR/r_arrival.txt"
fi

if [[ "$CCA" == "my_cca" ]]; then
  if [[ -f "$TMP_CONTEXT" ]]; then
    mv "$TMP_CONTEXT" "$OUTPUT_DIR/context.txt"
  else
    : > "$OUTPUT_DIR/context.txt"
  fi
  rmdir "$TMP_DIR" 2>/dev/null || true


  # Keep only cwnd log rows matching this client's IP and port.
  log "Filtering kernel log for $CLIENT_IP:$CLIENT_PORT"
  python3 "$FILTER_IP_PATH" \
    --input "$OUTPUT_DIR/context.txt" \
    --output "$FILTERED_CSV" \
    --ip "$CLIENT_IP" \
    --port "$CLIENT_PORT"

  # Produce a JSON summary from the filtered CSV.
  log "Extracting CSV summary"
  python3 "$EXTRACT_IP_INFO_PATH" \
    --input "$FILTERED_CSV" \
    --output "$INFO_JSON"

  # Plot cwnd evolution for this transfer.
  # - not specifying "--start-row" and "--end-row" will plot everything and this will take a lot of time
  log "Creating CWND graph"
  python3 "$EXTRACT_IP_CWND_PATH" \
    --input "$FILTERED_CSV" \
    --output "$CWND_PNG" \
    --ip "$CLIENT_IP" \
    --port "$CLIENT_PORT" \
    --start-row 1 \
    --end-row 500
else
  log "Using kernel CCA $CCA, AnalysisResult won't be ran."
fi

# Final paths and key transfer info.
log "Done"
printf 'Results: %s\n' "$OUTPUT_DIR"
if [[ -f "$OUTPUT_DIR/cumulative_server_summary.json" ]]; then
  printf 'Cumulative probe server summary: %s\n' "$OUTPUT_DIR/cumulative_server_summary.json"
elif [[ "$CUMULATIVE_ENABLED" == "1" ]]; then
  printf 'Cumulative probe server summary: N/A (probe did not complete)\n'
fi
printf 'Client: %s:%s\n' "$CLIENT_IP" "$CLIENT_PORT"
printf 'Elapsed seconds: %s\n' "$ELAPSED_SECONDS"
print_final_metrics "$OUTPUT_DIR/transfer_summary.json" "$INFO_JSON" "$OUTPUT_DIR/server.log"
