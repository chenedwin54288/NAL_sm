#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEHE_DIR="$SCRIPT_DIR/wehe-py3"
CLIENT_SERVER_RUN="$SCRIPT_DIR/client_server/run.sh"

WEHE_IMAGE="wehe"
WEHE_HOST="192.168.88.254"
WEHE_INTERFACE=""
WEHE_READY_PORTS="55556 56566 80 443"
WEHE_READY_TIMEOUT="120"
BUILD_WEHE=1
WEHE_CONTAINER_ID=""
CLIENT_SERVER_ARGS=(--cca my_cca --cwnd 0)

usage() {
  cat <<USAGE
Usage:
  $0 [server-wrapper-options] [-- client_server/run.sh options]

Workflow:
  1. Build the WeHe Docker image.
  2. Start the WeHe server container and remember its Docker container ID.
  3. Wait for WeHe ports to accept connections.
  4. Run integration/client_server/run.sh and wait for it to finish.
  5. Stop the WeHe container.

Server wrapper options:
  --wehe-host HOST          WeHe public hostname/IP passed to Docker (default: 192.168.88.254)
  --wehe-interface IFACE    Optional interface passed as the second startserver.sh argument
  --wehe-image NAME         Docker image tag to build/run (default: wehe)
  --wehe-ready-ports LIST   Space/comma-separated ports to wait for (default: 55556 56566 80 443)
  --wehe-ready-timeout SEC  Seconds to wait for WeHe readiness (default: 120)
  --no-build                Skip docker build and run the existing image
  --build                   Build the WeHe image before running (default)
  -h, --help                Show this help

All experiment arguments are passed through to integration/client_server/run.sh.
By default this wrapper passes --cca my_cca --cwnd 0, so the custom CCA is used
with its sender-side CWND cap disabled. If you pass later --cca or --cwnd values,
client_server/run.sh will use those later values.

Example:
  $0 --wehe-host 192.168.88.254 -- \\
    --size-gib 1 \\
    --rtt-ms 0.4 \\
    --rate-mbit 250 \\
    --tbf-rate 250Mbit \\
    --tbf-burst 50000b \\
    --tbf-limit 6250b
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

cleanup() {
  local status=$?
  if [[ -n "${WEHE_CONTAINER_ID:-}" ]]; then
    log "Stopping WeHe container $WEHE_CONTAINER_ID"
    sudo docker stop "$WEHE_CONTAINER_ID" >/dev/null 2>&1 || true
  fi
  return "$status"
}

show_wehe_logs() {
  if [[ -n "${WEHE_CONTAINER_ID:-}" ]]; then
    sudo docker logs --tail 80 "$WEHE_CONTAINER_ID" 2>/dev/null || true
  fi
}

container_is_running() {
  [[ "$(sudo docker inspect -f '{{.State.Running}}' "$WEHE_CONTAINER_ID" 2>/dev/null || true)" == "true" ]]
}

port_is_open() {
  local host="$1"
  local port="$2"
  python3 - "$host" "$port" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(1.0)
try:
    sock.connect((host, port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

wait_for_container_running() {
  local deadline=$((SECONDS + WEHE_READY_TIMEOUT))
  until container_is_running; do
    if (( SECONDS >= deadline )); then
      show_wehe_logs
      die "WeHe container did not enter running state within ${WEHE_READY_TIMEOUT}s"
    fi
    sleep 1
  done
}

wait_for_wehe_ports() {
  local deadline=$((SECONDS + WEHE_READY_TIMEOUT))
  local ports=("$@")
  local missing=()
  local port

  if [[ ${#ports[@]} -eq 0 ]]; then
    return
  fi

  while true; do
    missing=()
    for port in "${ports[@]}"; do
      if ! port_is_open "$WEHE_HOST" "$port"; then
        missing+=("$port")
      fi
    done

    if [[ ${#missing[@]} -eq 0 ]]; then
      return
    fi

    if ! container_is_running; then
      show_wehe_logs
      die "WeHe container exited before ports were ready: ${missing[*]}"
    fi

    if (( SECONDS >= deadline )); then
      show_wehe_logs
      die "Timed out waiting for WeHe ports on $WEHE_HOST: ${missing[*]}"
    fi

    sleep 1
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --wehe-host)
      WEHE_HOST="${2:-}"; shift 2 ;;
    --wehe-interface)
      WEHE_INTERFACE="${2:-}"; shift 2 ;;
    --wehe-image)
      WEHE_IMAGE="${2:-}"; shift 2 ;;
    --wehe-ready-ports)
      WEHE_READY_PORTS="${2//,/ }"; shift 2 ;;
    --wehe-ready-timeout)
      WEHE_READY_TIMEOUT="${2:-}"; shift 2 ;;
    --no-build)
      BUILD_WEHE=0; shift ;;
    --build)
      BUILD_WEHE=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    --)
      shift
      CLIENT_SERVER_ARGS+=("$@")
      break ;;
    *)
      CLIENT_SERVER_ARGS+=("$1")
      shift ;;
  esac
done

[[ -n "$WEHE_HOST" ]] || die "--wehe-host cannot be empty"
[[ -n "$WEHE_IMAGE" ]] || die "--wehe-image cannot be empty"
is_positive_int "$WEHE_READY_TIMEOUT" || die "--wehe-ready-timeout must be a positive integer"

read -r -a READY_PORT_ARRAY <<< "$WEHE_READY_PORTS"
for port in "${READY_PORT_ARRAY[@]}"; do
  is_positive_int "$port" || die "invalid WeHe ready port: $port"
done

need_command sudo
need_command docker
need_command python3

[[ -d "$WEHE_DIR" ]] || die "WeHe directory not found: $WEHE_DIR"
[[ -x "$CLIENT_SERVER_RUN" ]] || die "client_server run script is not executable: $CLIENT_SERVER_RUN"

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [[ "$BUILD_WEHE" == "1" ]]; then
  log "Building WeHe Docker image '$WEHE_IMAGE'"
  sudo docker build -t "$WEHE_IMAGE" "$WEHE_DIR"
else
  log "Skipping Docker build; using existing image '$WEHE_IMAGE'"
fi

DOCKER_RUN_CMD=(
  sudo docker run
  -v "$WEHE_DIR/ssl:/wehe/ssl"
  --net=host
  --env "SUDO_UID=$UID"
  -d
  "$WEHE_IMAGE"
  "$WEHE_HOST"
)
if [[ -n "$WEHE_INTERFACE" ]]; then
  DOCKER_RUN_CMD+=("$WEHE_INTERFACE")
fi

log "Starting WeHe server container"
WEHE_CONTAINER_ID="$("${DOCKER_RUN_CMD[@]}")"
printf 'WeHe container ID: %s\n' "$WEHE_CONTAINER_ID"

log "Waiting for WeHe container to run"
wait_for_container_running

log "Waiting for WeHe ports on $WEHE_HOST: ${READY_PORT_ARRAY[*]}"
wait_for_wehe_ports "${READY_PORT_ARRAY[@]}"

log "Starting client_server/run.sh"
"$CLIENT_SERVER_RUN" "${CLIENT_SERVER_ARGS[@]}"

log "client_server finished"
