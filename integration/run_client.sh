#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEHE_CLIENT_DIR="$SCRIPT_DIR/client/wehe-cmdline"
WEHE_JAR="$WEHE_CLIENT_DIR/wehe-cmdline.jar"
CLIENT_PY="$SCRIPT_DIR/client/client.py"
RWND_HELPER="$SCRIPT_DIR/wehe_result_to_rwnd.py"

REPLAY_NAME="amazon"
WEHE_SERVER="192.168.88.254"
CLIENT_SERVER_HOST="192.168.88.254"
CLIENT_SERVER_PORT="9000"
RESULTS_DIR="$WEHE_CLIENT_DIR/results"
LOG_LEVEL="info"
RTT_MS="0.4"
MSS_BYTES="1460"
QUEUE_BYTES=""
THROUGHPUT_FIELD="xput_avg_original"
RWND_SEGMENTS=""
USE_SUDO_JAVA=1
JAVA_BIN="java"

usage() {
  cat <<USAGE
Usage:
  $0 [options]

Workflow:
  1. Run the WeHe command-line replay.
  2. Extract the newest WeHe throughput result.
  3. Compute an rwnd segment count.
  4. Start integration/client/client.py with --rwnd-segments.

Options:
  --replay NAME              WeHe replay name (default: amazon)
  --wehe-server HOST         WeHe server hostname/IP (default: 192.168.88.254)
  --client-server-host HOST  client_server host for client.py (default: 192.168.88.254)
  --client-server-port PORT  client_server port for client.py (default: 9000)
  --results-dir DIR          WeHe results directory (default: client/wehe-cmdline/results)
  --log-level LEVEL          WeHe log level (default: info)

  --rtt-ms N                 RTT used for the rwnd BDP calculation (default: 0.4)
  --mss-bytes N              MSS used for --rwnd-segments (default: 1460)
  --queue-bytes VALUE        Optional queue/TBF limit, for example 50000b
  --tbf-limit VALUE          Alias for --queue-bytes
  --throughput-field FIELD   WeHe JSON throughput field (default: xput_avg_original)
  --rwnd-segments N          Skip calculation and use this rwnd segment count

  --sudo-java                Run the WeHe Java client with sudo (default)
  --no-sudo-java             Run the WeHe Java client without sudo
  --java-bin PATH            Java binary to execute (default: java)
  -h, --help                 Show this help

Example:
  $0 --wehe-server 192.168.88.254 --client-server-host 192.168.88.254 --rtt-ms 0.4 --queue-bytes 50000b
USAGE
}

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

is_positive_int() {
  [[ "$1" =~ ^[0-9]+$ ]] && (( "$1" > 0 ))
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --replay)
      REPLAY_NAME="${2:-}"; shift 2 ;;
    --wehe-server)
      WEHE_SERVER="${2:-}"; shift 2 ;;
    --client-server-host)
      CLIENT_SERVER_HOST="${2:-}"; shift 2 ;;
    --client-server-port)
      CLIENT_SERVER_PORT="${2:-}"; shift 2 ;;
    --results-dir)
      RESULTS_DIR="${2:-}"; shift 2 ;;
    --log-level)
      LOG_LEVEL="${2:-}"; shift 2 ;;
    --rtt-ms)
      RTT_MS="${2:-}"; shift 2 ;;
    --mss-bytes)
      MSS_BYTES="${2:-}"; shift 2 ;;
    --queue-bytes|--tbf-limit)
      QUEUE_BYTES="${2:-}"; shift 2 ;;
    --throughput-field)
      THROUGHPUT_FIELD="${2:-}"; shift 2 ;;
    --rwnd-segments)
      RWND_SEGMENTS="${2:-}"; shift 2 ;;
    --sudo-java)
      USE_SUDO_JAVA=1; shift ;;
    --no-sudo-java)
      USE_SUDO_JAVA=0; shift ;;
    --java-bin)
      JAVA_BIN="${2:-}"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      die "unknown option: $1" ;;
  esac
done

[[ -n "$REPLAY_NAME" ]] || die "--replay cannot be empty"
[[ -n "$WEHE_SERVER" ]] || die "--wehe-server cannot be empty"
[[ -n "$CLIENT_SERVER_HOST" ]] || die "--client-server-host cannot be empty"
is_positive_int "$CLIENT_SERVER_PORT" || die "--client-server-port must be a positive integer"
is_positive_int "$MSS_BYTES" || die "--mss-bytes must be a positive integer"
if [[ -n "$RWND_SEGMENTS" ]]; then
  is_positive_int "$RWND_SEGMENTS" || die "--rwnd-segments must be a positive integer"
fi

need_command "$JAVA_BIN"
need_command python3
if [[ "$USE_SUDO_JAVA" == "1" ]]; then
  need_command sudo
fi

[[ -f "$WEHE_JAR" ]] || die "WeHe jar not found: $WEHE_JAR"
[[ -f "$CLIENT_PY" ]] || die "client.py not found: $CLIENT_PY"
[[ -f "$RWND_HELPER" ]] || die "rwnd helper not found: $RWND_HELPER"

mkdir -p "$RESULTS_DIR/logs" "$RESULTS_DIR/ui"
RESULTS_DIR="$(cd "$RESULTS_DIR" && pwd)"

RUN_STARTED_AT="$(date +%s)"
WEHE_CMD=(
  "$JAVA_BIN"
  -jar "$WEHE_JAR"
  -n "$REPLAY_NAME"
  -s "$WEHE_SERVER"
  -r "$RESULTS_DIR/"
  -l "$LOG_LEVEL"
)
if [[ "$USE_SUDO_JAVA" == "1" ]]; then
  WEHE_CMD=(sudo "${WEHE_CMD[@]}")
fi

log "Running WeHe replay '$REPLAY_NAME' against $WEHE_SERVER"
(
  cd "$WEHE_CLIENT_DIR"
  "${WEHE_CMD[@]}"
)

if [[ -z "$RWND_SEGMENTS" ]]; then
  RWND_CMD=(
    python3 "$RWND_HELPER"
    --results-dir "$RESULTS_DIR"
    --since-epoch "$RUN_STARTED_AT"
    --throughput-field "$THROUGHPUT_FIELD"
    --rtt-ms "$RTT_MS"
    --mss-bytes "$MSS_BYTES"
  )
  if [[ -n "$QUEUE_BYTES" ]]; then
    RWND_CMD+=(--queue-bytes "$QUEUE_BYTES")
  fi

  log "Computing rwnd from WeHe throughput"
  "${RWND_CMD[@]}"
  RWND_SEGMENTS="$("${RWND_CMD[@]}" --value-only)"
fi

log "Starting client.py with rwnd=$RWND_SEGMENTS segments"
python3 "$CLIENT_PY" \
  --host "$CLIENT_SERVER_HOST" \
  --port "$CLIENT_SERVER_PORT" \
  --rwnd-segments "$RWND_SEGMENTS" \
  --mss-bytes "$MSS_BYTES"
