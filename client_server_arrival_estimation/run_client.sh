#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CUMULATIVE_CLIENT_PATH="$SCRIPT_DIR/client/client_cumulative.py"
NORMAL_CLIENT_PATH="$SCRIPT_DIR/client/client.py"

SERVER_HOST="192.168.88.254"
SERVER_PORT="9000"
CUMULATIVE_PORT="9001"
RTT_MS="0.4"
BASE_OWD_MS=""
TBF_RATE=""
TBF_LIMIT=""
MSS_BYTES="1460"
RWND_GAIN="1.0"
RECV_SIZE="64KiB"
PROBE_FORMAT="framed"
ESTIMATION_WINDOW_SIZE="20"
OUTPUT_DIR=""

usage() {
  cat <<USAGE
Usage:
  $0 [options]

Options:
  --host HOST              Server host (default: 192.168.88.254)
  --port PORT              Normal server port (default: 9000)
  --cumulative-port PORT   Cumulative probe server port (default: 9001)
  --probe-format FORMAT    Cumulative probe format: framed or raw (default: framed)
  --rtt-ms N               RTT_base in ms (default: 400)
  --base-owd-ms N          Optional explicit one-way base delay in ms
  --tbf-rate RATE          Known TBF service rate, for example 100Mbit
  --tbf-limit BYTES        Known TBF queue size Q_config, for example 6250b
  --mss-bytes N            MSS used for rwnd segment display (default: 1460)
  --rwnd-gain N            Multiplier applied to measured rwnd (default: 1.0)
  --recv-size N            Cumulative client recv size (default: 64KiB)
  --estimation-window-size N  Queue-growth regression window (default: 20)
  --output-dir DIR         Directory for cumulative CSV/summary

Example:
  $0 --host 192.168.88.254 --rtt-ms 0.4 --tbf-rate 100Mbit --tbf-limit 25000b
USAGE
}

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

is_positive_int() {
  [[ "$1" =~ ^[0-9]+$ ]] && (( "$1" > 0 ))
}

is_positive_float() {
  [[ "$1" =~ ^[0-9]+([.][0-9]+)?$ ]] && awk "BEGIN { exit !($1 > 0) }"
}

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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      SERVER_HOST="${2:-}"; shift 2 ;;
    --port)
      SERVER_PORT="${2:-}"; shift 2 ;;
    --cumulative-port)
      CUMULATIVE_PORT="${2:-}"; shift 2 ;;
    --probe-format)
      PROBE_FORMAT="${2:-}"; shift 2 ;;
    --rtt-ms)
      RTT_MS="${2:-}"; shift 2 ;;
    --base-owd-ms)
      BASE_OWD_MS="${2:-}"; shift 2 ;;
    --tbf-rate)
      TBF_RATE="${2:-}"; shift 2 ;;
    --tbf-limit)
      TBF_LIMIT="${2:-}"; shift 2 ;;
    --mss-bytes)
      MSS_BYTES="${2:-}"; shift 2 ;;
    --rwnd-gain)
      RWND_GAIN="${2:-}"; shift 2 ;;
    --recv-size)
      RECV_SIZE="${2:-}"; shift 2 ;;
    --estimation-window-size)
      ESTIMATION_WINDOW_SIZE="${2:-}"; shift 2 ;;
    --output-dir)
      OUTPUT_DIR="${2:-}"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      die "unknown option: $1" ;;
  esac
done

command -v python3 >/dev/null 2>&1 || die "required command not found: python3"
[[ -f "$CUMULATIVE_CLIENT_PATH" ]] || die "cumulative client not found: $CUMULATIVE_CLIENT_PATH"
[[ -f "$NORMAL_CLIENT_PATH" ]] || die "normal client not found: $NORMAL_CLIENT_PATH"

is_positive_int "$SERVER_PORT" || die "--port must be a positive integer"
is_positive_int "$CUMULATIVE_PORT" || die "--cumulative-port must be a positive integer"
is_positive_int "$MSS_BYTES" || die "--mss-bytes must be a positive integer"
is_positive_int "$ESTIMATION_WINDOW_SIZE" || die "--estimation-window-size must be a positive integer"
is_positive_float "$RTT_MS" || die "--rtt-ms must be positive"
[[ "$PROBE_FORMAT" == "framed" || "$PROBE_FORMAT" == "raw" ]] || die "--probe-format must be framed or raw"
if [[ -n "$BASE_OWD_MS" ]]; then
  [[ "$BASE_OWD_MS" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "--base-owd-ms must be non-negative"
fi
if [[ -n "$TBF_RATE$TBF_LIMIT" ]]; then
  [[ -n "$TBF_RATE" && -n "$TBF_LIMIT" ]] || die "set --tbf-rate and --tbf-limit together"
  [[ "$PROBE_FORMAT" == "framed" ]] || die "--tbf-rate/--tbf-limit require --probe-format framed"
fi

if [[ -z "$OUTPUT_DIR" ]]; then
  RUN_ID="$(date +%Y%m%d_%H%M%S)"
  OUTPUT_DIR="$SCRIPT_DIR/client/cumulative_runs/$RUN_ID"
fi
mkdir -p "$OUTPUT_DIR"

CUMULATIVE_CSV="$OUTPUT_DIR/cumulative_arrival.csv"
CUMULATIVE_SUMMARY="$OUTPUT_DIR/cumulative_client_summary.json"

log "Running cumulative probe client against $SERVER_HOST:$CUMULATIVE_PORT"
CUMULATIVE_CLIENT_CMD=(
  python3 "$CUMULATIVE_CLIENT_PATH"
  --host "$SERVER_HOST"
  --port "$CUMULATIVE_PORT"
  --probe-format "$PROBE_FORMAT"
  --recv-size "$RECV_SIZE"
  --output-file "$CUMULATIVE_CSV"
  --summary-file "$CUMULATIVE_SUMMARY"
  --rtt-ms "$RTT_MS"
  --mss-bytes "$MSS_BYTES"
  --rwnd-gain "$RWND_GAIN"
  --estimation-window-size "$ESTIMATION_WINDOW_SIZE"
)
if [[ -n "$BASE_OWD_MS" ]]; then
  CUMULATIVE_CLIENT_CMD+=(--base-owd-ms "$BASE_OWD_MS")
fi
if [[ -n "$TBF_RATE" ]]; then
  CUMULATIVE_CLIENT_CMD+=(--tbf-rate "$TBF_RATE" --tbf-limit "$TBF_LIMIT")
fi
"${CUMULATIVE_CLIENT_CMD[@]}"

[[ -f "$CUMULATIVE_SUMMARY" ]] || die "cumulative client did not write summary: $CUMULATIVE_SUMMARY"
RWND_BYTES="$(json_field "$CUMULATIVE_SUMMARY" recommended_rwnd_bytes)"
[[ "$RWND_BYTES" =~ ^[0-9]+$ ]] || die "could not read recommended rwnd from summary"
(( RWND_BYTES > 0 )) || die "recommended rwnd must be positive"

log "Running normal client against $SERVER_HOST:$SERVER_PORT with rwnd=$RWND_BYTES bytes"
python3 "$NORMAL_CLIENT_PATH" \
  --host "$SERVER_HOST" \
  --port "$SERVER_PORT" \
  --rwnd-bytes "$RWND_BYTES"

log "Done"
printf 'Cumulative client artifacts: %s\n' "$OUTPUT_DIR"
printf 'Recommended rwnd bytes: %s\n' "$RWND_BYTES"
