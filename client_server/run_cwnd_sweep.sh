#!/usr/bin/env bash

set -euo pipefail

# Edit these values before starting a sweep.
QUEUE_SIZES=(6250, 12500, 25000, 50000, 100000)
TOKEN_GENERATION_RATES=(500 750 1000)
BURST_SIZES=(5840 12500 25000 50000 100000)

RTT_MS="0.4"
SIZE_GIB="1"
MSS_BYTES="1460"
CCA="my_cca"
SERVER_DEV="eno1"
SERVER_BIND_HOST="0.0.0.0"
SERVER_PORT="9000"
SERVER_IP_FOR_CLIENT="192.168.88.254"
LOG_INTERVAL="0.5"

# Run this script on nal-pc1. The client is started on nal-pc2 over SSH.
CLIENT_SSH_HOST="192.168.88.253"
CLIENT_SSH_USER="nal"
CLIENT_SSH_PORT="22"
CLIENT_WORKDIR="/home/nal/client_server"
CLIENT_SCRIPT_REL_PATH="client/client.py"
CLIENT_COMMAND=(python3 "$CLIENT_SCRIPT_REL_PATH")
CLIENT_EXTRA_ARGS=()
SSH_OPTS=(-o BatchMode=yes)
SSH_CONNECT_TIMEOUT_SECONDS=5

# Leave these arrays empty unless your local scripts support extra options.
RUN_SH_EXTRA_ARGS=()

# The password is only used to refresh sudo before run.sh starts.
# Prefer overriding it at runtime with: SUDO_PASSWORD=... ./run_cwnd_sweep.sh
SUDO_PASSWORD="${SUDO_PASSWORD:-NAL-123-neut}"

RENO_RUNS=1
FIXED_CWND_RUNS=1
EMPIRICAL_MAX_LOSS_RATE="0.05"
EMPIRICAL_MAX_PROBES=20
SERVER_READY_TIMEOUT_SECONDS=180
CLIENT_CONNECT_TIMEOUT_SECONDS=30
SERVER_SHUTDOWN_TIMEOUT_SECONDS=10

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SH="$SCRIPT_DIR/run.sh"
CALCULATION_PY="$SCRIPT_DIR/calculation.py"
RUN_ROOT="$SCRIPT_DIR/sweep_results/$(date +%Y%m%d_%H%M%S)"
README_FILE="$RUN_ROOT/README.md"
DETAILS_TSV="$RUN_ROOT/run-details.tsv"

ACTIVE_SERVER_PID=""
ACTIVE_CLIENT_PID=""
SUDO_KEEPALIVE_PID=""

log() {
  printf '==> %s\n' "$*" >&2
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

number_token() {
  local raw="$1"
  local name="$2"
  local value="${raw%,}"

  if [[ "$value" != "$raw" ]]; then
    log "stripped trailing comma from $name entry '$raw'; Bash arrays should use spaces, not commas"
  fi

  [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "invalid numeric entry in $name: $raw"
  printf '%s\n' "$value"
}

sudo_signal() {
  local signal="$1"
  local target="$2"

  if sudo -n true 2>/dev/null; then
    sudo -n kill "$signal" -- "$target" 2>/dev/null
  elif [[ -n "$SUDO_PASSWORD" ]]; then
    printf '%s\n' "$SUDO_PASSWORD" | sudo -S -p '' kill "$signal" -- "$target" 2>/dev/null
  else
    kill "$signal" -- "$target" 2>/dev/null
  fi
}

sudo_run() {
  if [[ -n "$SUDO_PASSWORD" ]]; then
    printf '%s\n' "$SUDO_PASSWORD" | sudo -S -p '' "$@"
  else
    sudo "$@"
  fi
}

process_group_exists() {
  local pid="$1"
  sudo_signal -0 "-$pid"
}

terminate_process_group() {
  local pid="${1:-}"
  local deadline

  [[ -n "$pid" ]] || return 0

  sudo_signal -TERM "-$pid" || kill -TERM -- "$pid" 2>/dev/null || true

  deadline=$((SECONDS + 5))
  while (( SECONDS < deadline )); do
    process_group_exists "$pid" || break
    sleep 0.2
  done

  if process_group_exists "$pid"; then
    sudo_signal -KILL "-$pid" || kill -KILL -- "$pid" 2>/dev/null || true
  fi

  wait "$pid" 2>/dev/null || true
}

server_socket_listening() {
  command -v ss >/dev/null 2>&1 || return 1
  ss -H -ltn "sport = :$SERVER_PORT" 2>/dev/null | grep -q .
}

wait_for_server_socket_closed() {
  local deadline=$((SECONDS + SERVER_SHUTDOWN_TIMEOUT_SECONDS))

  while (( SECONDS < deadline )); do
    if ! server_socket_listening; then
      return 0
    fi
    sleep 0.2
  done

  ! server_socket_listening
}

force_close_server_socket() {
  local pid="${1:-}"

  terminate_process_group "$pid"

  if wait_for_server_socket_closed; then
    log "server socket on TCP/${SERVER_PORT} is closed"
  else
    log "server socket on TCP/${SERVER_PORT} is still listening after process-group kill"
    if command -v fuser >/dev/null 2>&1; then
      refresh_sudo || true
      sudo_run fuser -k -TERM -n tcp "$SERVER_PORT" >/dev/null 2>&1 || true
      wait_for_server_socket_closed || sudo_run fuser -k -KILL -n tcp "$SERVER_PORT" >/dev/null 2>&1 || true
    fi

    if wait_for_server_socket_closed; then
      log "server socket on TCP/${SERVER_PORT} is closed"
    else
      log "warning: TCP/${SERVER_PORT} still appears to be listening; check with: sudo ss -ltnp sport = :${SERVER_PORT}"
    fi
  fi

  sudo_run tc qdisc del dev "$SERVER_DEV" root 2>/dev/null || true
}

cleanup() {
  if [[ -n "${ACTIVE_CLIENT_PID:-}" ]] && kill -0 "$ACTIVE_CLIENT_PID" 2>/dev/null; then
    kill "$ACTIVE_CLIENT_PID" 2>/dev/null || true
    wait "$ACTIVE_CLIENT_PID" 2>/dev/null || true
  fi

  if [[ -n "${ACTIVE_SERVER_PID:-}" ]]; then
    force_close_server_socket "$ACTIVE_SERVER_PID"
  fi

  if [[ -n "${SUDO_KEEPALIVE_PID:-}" ]] && kill -0 "$SUDO_KEEPALIVE_PID" 2>/dev/null; then
    kill "$SUDO_KEEPALIVE_PID" 2>/dev/null || true
    wait "$SUDO_KEEPALIVE_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

refresh_sudo() {
  if [[ -n "$SUDO_PASSWORD" ]]; then
    sudo_run -v >/dev/null
  else
    sudo -v
  fi
}

start_sudo_keepalive() {
  (
    while true; do
      sudo -n true 2>/dev/null || refresh_sudo
      sleep 30
    done
  ) &
  SUDO_KEEPALIVE_PID=$!
}

quote_remote_client_command() {
  local quoted_workdir
  local quoted_arg
  local quoted_marker
  local command_text=""
  local client_args=(
    "${CLIENT_COMMAND[@]}"
    --host "$SERVER_IP_FOR_CLIENT"
    --port "$SERVER_PORT"
    "${CLIENT_EXTRA_ARGS[@]}"
  )

  printf -v quoted_workdir '%q' "$CLIENT_WORKDIR"
  for arg in "${client_args[@]}"; do
    printf -v quoted_arg '%q' "$arg"
    if [[ -z "$command_text" ]]; then
      command_text="$quoted_arg"
    else
      command_text+=" $quoted_arg"
    fi
  done

  printf -v quoted_marker '%q' "[client] starting"
  printf 'printf %%s\\\\n %s; cd %s && exec %s' "$quoted_marker" "$quoted_workdir" "$command_text"
}

ssh_target() {
  if [[ -n "${CLIENT_SSH_USER:-}" ]]; then
    printf '%s@%s\n' "$CLIENT_SSH_USER" "$CLIENT_SSH_HOST"
  else
    printf '%s\n' "$CLIENT_SSH_HOST"
  fi
}

quote_ssh_preflight_command() {
  local quoted_workdir
  local quoted_client_script
  printf -v quoted_workdir '%q' "$CLIENT_WORKDIR"
  printf -v quoted_client_script '%q' "$CLIENT_SCRIPT_REL_PATH"
  printf 'if ! cd %s; then echo "preflight: CLIENT_WORKDIR does not exist: %s"; exit 20; fi; if ! command -v python3 >/dev/null; then echo "preflight: python3 not found on client"; exit 21; fi; if ! test -f %s; then echo "preflight: %s not found under $(pwd)"; find /home/nal -maxdepth 4 -type f -path "*/client.py" 2>/dev/null | head -20; exit 22; fi; printf %%s\\\\n ssh-client-preflight-ok' "$quoted_workdir" "$CLIENT_WORKDIR" "$quoted_client_script" "$CLIENT_SCRIPT_REL_PATH"
}

check_client_ssh() {
  local preflight_command
  local preflight_output

  preflight_command="$(quote_ssh_preflight_command)"
  log "checking SSH client access on $(ssh_target):$CLIENT_SSH_PORT"

  if ! preflight_output="$(
      ssh "${SSH_OPTS[@]}" -o ConnectTimeout="$SSH_CONNECT_TIMEOUT_SECONDS" \
        -p "$CLIENT_SSH_PORT" "$(ssh_target)" "$preflight_command" 2>&1
    )"; then
    if [[ -n "$preflight_output" ]]; then
      printf '%s\n' "$preflight_output" >&2
    fi
    die "cannot run client over SSH on $(ssh_target):$CLIENT_SSH_PORT. Check CLIENT_SSH_HOST, CLIENT_SSH_USER, CLIENT_SSH_PORT, SSH keys, and CLIENT_WORKDIR before starting the sweep."
  fi

  [[ "$preflight_output" == *"ssh-client-preflight-ok"* ]] || \
    die "SSH preflight connected, but did not confirm python3 and $CLIENT_SCRIPT_REL_PATH in CLIENT_WORKDIR=$CLIENT_WORKDIR"
}

wait_for_server_ready() {
  local log_file="$1"
  local server_pid="$2"
  local deadline=$((SECONDS + SERVER_READY_TIMEOUT_SECONDS))

  while (( SECONDS < deadline )); do
    if [[ -f "$log_file" ]] && grep -q 'Listening on .*:' "$log_file"; then
      return 0
    fi

    if ! kill -0 "$server_pid" 2>/dev/null; then
      return 1
    fi

    sleep 0.2
  done

  return 1
}

wait_for_client_connected() {
  local server_log="$1"
  local server_pid="$2"
  local client_pid="$3"
  local deadline=$((SECONDS + CLIENT_CONNECT_TIMEOUT_SECONDS))

  while (( SECONDS < deadline )); do
    if [[ -f "$server_log" ]] && grep -q 'Client connected from' "$server_log"; then
      return 0
    fi

    if ! kill -0 "$server_pid" 2>/dev/null; then
      return 1
    fi

    if ! kill -0 "$client_pid" 2>/dev/null; then
      sleep 0.2
      [[ -f "$server_log" ]] && grep -q 'Client connected from' "$server_log" && return 0
      return 1
    fi

    sleep 0.2
  done

  return 1
}

extract_result_dir() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

result = ""
for line in Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("Results: "):
        result = line.split("Results: ", 1)[1].strip()

print(result)
PY
}

calculate_cwnds() {
  python3 - "$CALCULATION_PY" "$1" "$RTT_MS" "$2" "$MSS_BYTES" <<'PY'
import importlib.util
import math
import sys

calculation_path, rate_mbit, rtt_ms, queue_bytes, mss_bytes = sys.argv[1:]
rate_mbit = float(rate_mbit)
rtt_seconds = float(rtt_ms) / 1000.0
queue_bytes = float(queue_bytes)
mss_bytes = int(mss_bytes)

spec = importlib.util.spec_from_file_location("calculation", calculation_path)
calculation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculation)

result = calculation.calculate_cwnd(
    r_tbf_bps=rate_mbit * 1_000_000.0,
    rtt_seconds=rtt_seconds,
    q_config_bytes=queue_bytes,
    mss_bytes=mss_bytes,
    r_arrival_bps=None,
)

bdp_cwnd = max(1, math.floor(result["bdp_bytes"] / mss_bytes))
bdp_plus_queue_cwnd = result["original_cwnd"]
print(f"{bdp_cwnd}\t{bdp_plus_queue_cwnd}")
PY
}

result_metrics() {
  python3 - "$1" "$2" "$3" <<'PY'
import csv
import json
import statistics
import sys
from pathlib import Path

result_dir = Path(sys.argv[1])
configured_cwnd = sys.argv[2]
mode = sys.argv[3]
loss_phases = {"loss_recovery", "fast_retransmit"}


def read_json(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def maybe_float(value):
    if value is None or value == "":
        return None
    return float(value)


def maybe_int(value):
    if value is None or value == "":
        return None
    return int(float(value))


def read_rows(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


summary = read_json(result_dir / "transfer_summary.json")
ip_info = read_json(result_dir / "ip_info.json")
rows = read_rows(result_dir / "filtered_context.csv")

throughput = maybe_float(summary.get("post_slow_start_mib_per_second"))
if throughput is None:
    throughput = maybe_float(ip_info.get("post_slow_start_mib_per_second"))
if throughput is None:
    throughput = maybe_float(summary.get("mib_per_second"))
if throughput is None:
    throughput = 0.0

phase_counts = ip_info.get("phase_counts", {})
row_count = int(ip_info.get("row_count") or 0)
loss_rows = sum(int(phase_counts.get(phase) or 0) for phase in loss_phases)
loss_rate = (loss_rows / row_count) if row_count else 0.0

post_slow_start_rows = []
seen_slow_start = False
for row in rows:
    phase = (row.get("phase") or "").lower()
    if phase == "slow_start":
        seen_slow_start = True
        continue
    if seen_slow_start or not rows:
        post_slow_start_rows.append(row)

if not post_slow_start_rows:
    post_slow_start_rows = rows

cwnds = [maybe_int(row.get("cwnd")) for row in post_slow_start_rows]
cwnds = [value for value in cwnds if value is not None]
top_cwnds = []
for left, right in zip(cwnds, cwnds[1:]):
    if left > right:
        top_cwnds.append(left)

avg_top_cwnd = statistics.mean(top_cwnds) if top_cwnds else (max(cwnds) if cwnds else 0.0)
first_loss_cwnd = ""
for row in post_slow_start_rows:
    if (row.get("phase") or "").lower() in loss_phases:
        value = maybe_int(row.get("cwnd"))
        if value is not None:
            first_loss_cwnd = str(value)
            break

if mode == "reno":
    display_cwnd = f"{avg_top_cwnd:.2f}"
else:
    display_cwnd = configured_cwnd

print(
    "\t".join(
        [
            display_cwnd,
            f"{throughput:.2f}",
            f"{loss_rate:.6f}",
            str(row_count),
            str(loss_rows),
            first_loss_cwnd,
            f"{avg_top_cwnd:.2f}",
        ]
    )
)
PY
}

float_le() {
  python3 - "$1" "$2" <<'PY'
import sys
raise SystemExit(0 if float(sys.argv[1]) <= float(sys.argv[2]) else 1)
PY
}

float_gt() {
  python3 - "$1" "$2" <<'PY'
import sys
raise SystemExit(0 if float(sys.argv[1]) > float(sys.argv[2]) else 1)
PY
}

average_values() {
  python3 - "$@" <<'PY'
import sys
values = [float(value) for value in sys.argv[1:] if value != ""]
print(f"{(sum(values) / len(values)):.2f}" if values else "0.00")
PY
}

floor_cwnd() {
  python3 - "$1" "$2" <<'PY'
import sys
value = sys.argv[1]
fallback = int(sys.argv[2])
try:
    cwnd = int(float(value))
except ValueError:
    cwnd = fallback
print(max(1, int(cwnd)))
PY
}

format_cell() {
  local cwnd="$1"
  local throughput="$2"
  local suffix="${3:-}"
  printf '<%s, %s>%s' "$cwnd" "$throughput" "$suffix"
}

run_single() {
  local mode="$1"
  local configured_cwnd="$2"
  local rate_mbit="$3"
  local queue_bytes="$4"
  local burst_bytes="$5"
  local attempt="$6"
  local slug="${queue_bytes}q_${burst_bytes}burst_${rate_mbit}mbit_${mode}_${configured_cwnd}_run${attempt}"
  local artifact_dir="$RUN_ROOT/logs/$slug"
  local server_log="$artifact_dir/server-wrapper.log"
  local client_log="$artifact_dir/client.log"
  local remote_command
  local client_rc
  local server_rc
  local result_dir
  local metrics

  mkdir -p "$artifact_dir"
  log "rate=${rate_mbit}Mbit queue=${queue_bytes} burst=${burst_bytes} mode=${mode} cwnd=${configured_cwnd} run=${attempt}"

  refresh_sudo
  SUDO_PASSWORD="$SUDO_PASSWORD" PYTHONUNBUFFERED=1 setsid stdbuf -oL -eL "$RUN_SH" \
    --cca "$CCA" \
    --size-gib "$SIZE_GIB" \
    --host "$SERVER_BIND_HOST" \
    --port "$SERVER_PORT" \
    --dev "$SERVER_DEV" \
    --log-interval "$LOG_INTERVAL" \
    --rtt-ms "$RTT_MS" \
    --rate-mbit "$rate_mbit" \
    --tbf-rate "${rate_mbit}Mbit" \
    --tbf-burst "${burst_bytes}b" \
    --tbf-limit "${queue_bytes}b" \
    --mss-bytes "$MSS_BYTES" \
    --cwnd "$configured_cwnd" \
    "${RUN_SH_EXTRA_ARGS[@]}" \
    >"$server_log" 2>&1 &

  ACTIVE_SERVER_PID=$!

  if ! wait_for_server_ready "$server_log" "$ACTIVE_SERVER_PID"; then
    force_close_server_socket "$ACTIVE_SERVER_PID"
    ACTIVE_SERVER_PID=""
    tail -n 80 "$server_log" >&2 || true
    die "server did not become ready; see $server_log"
  fi

  remote_command="$(quote_remote_client_command)"
  printf 'Starting SSH client at %s\n' "$(date -Is)" >"$client_log"
  ssh "${SSH_OPTS[@]}" -p "$CLIENT_SSH_PORT" "$(ssh_target)" "$remote_command" >>"$client_log" 2>&1 &
  ACTIVE_CLIENT_PID=$!
  log "client SSH started with PID $ACTIVE_CLIENT_PID; waiting for server accept"

  if ! wait_for_client_connected "$server_log" "$ACTIVE_SERVER_PID" "$ACTIVE_CLIENT_PID"; then
    kill "$ACTIVE_CLIENT_PID" 2>/dev/null || true
    wait "$ACTIVE_CLIENT_PID" 2>/dev/null || true
    force_close_server_socket "$ACTIVE_SERVER_PID"
    wait "$ACTIVE_SERVER_PID" 2>/dev/null || true
    ACTIVE_CLIENT_PID=""
    ACTIVE_SERVER_PID=""
    tail -n 80 "$server_log" >&2 || true
    tail -n 80 "$client_log" >&2 || true
    die "client did not connect within ${CLIENT_CONNECT_TIMEOUT_SECONDS}s; see $server_log and $client_log"
  fi

  log "server accepted client connection"

  if wait "$ACTIVE_CLIENT_PID"; then
    client_rc=0
  else
    client_rc=$?
  fi
  ACTIVE_CLIENT_PID=""

  if (( client_rc != 0 )); then
    force_close_server_socket "$ACTIVE_SERVER_PID"
    ACTIVE_SERVER_PID=""
    tail -n 80 "$client_log" >&2 || true
    die "client failed with exit code $client_rc; see $client_log"
  fi

  if wait "$ACTIVE_SERVER_PID"; then
    server_rc=0
  else
    server_rc=$?
  fi
  ACTIVE_SERVER_PID=""

  if (( server_rc != 0 )); then
    tail -n 80 "$server_log" >&2 || true
    die "server run failed with exit code $server_rc; see $server_log"
  fi

  result_dir="$(extract_result_dir "$server_log")"
  [[ -n "$result_dir" ]] || die "could not find Results: line in $server_log"
  [[ -d "$result_dir" ]] || die "result directory does not exist: $result_dir"

  metrics="$(result_metrics "$result_dir" "$configured_cwnd" "$mode")"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$queue_bytes" "$burst_bytes" "$rate_mbit" "$mode" "$configured_cwnd" "$attempt" "$metrics" \
    "$result_dir" "$server_log" "$client_log" >>"$DETAILS_TSV"

  printf '%s\t%s\t%s\t%s\n' "$metrics" "$result_dir" "$server_log" "$client_log"
}

run_repeated() {
  local mode="$1"
  local configured_cwnd="$2"
  local run_count="$3"
  local rate_mbit="$4"
  local queue_bytes="$5"
  local burst_bytes="$6"
  local display_values=()
  local throughput_values=()
  local loss_values=()
  local first_loss_cwnd=""
  local avg_top_cwnd=""
  local attempt
  local run_output
  local display_cwnd throughput loss_rate row_count loss_rows first_loss avg_top result_dir server_log client_log

  for ((attempt = 1; attempt <= run_count; attempt++)); do
    if ! run_output="$(
      run_single "$mode" "$configured_cwnd" "$rate_mbit" "$queue_bytes" "$burst_bytes" "$attempt"
    )"; then
      return 1
    fi
    IFS=$'\t' read -r display_cwnd throughput loss_rate row_count loss_rows first_loss avg_top result_dir server_log client_log <<<"$run_output"
    display_values+=("$display_cwnd")
    throughput_values+=("$throughput")
    loss_values+=("$loss_rate")
    [[ -z "$first_loss_cwnd" && -n "$first_loss" ]] && first_loss_cwnd="$first_loss"
    avg_top_cwnd="$avg_top"
  done

  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$(average_values "${display_values[@]}")" \
    "$(average_values "${throughput_values[@]}")" \
    "$(average_values "${loss_values[@]}")" \
    "$first_loss_cwnd" \
    "$avg_top_cwnd"
}

empirical_start_cwnd() {
  local avg_top_cwnd="$1"
  local fallback_cwnd="$2"

  floor_cwnd "$avg_top_cwnd" "$fallback_cwnd"
}

empirical_search() {
  local start_cwnd="$1"
  local rate_mbit="$2"
  local queue_bytes="$3"
  local burst_bytes="$4"
  local candidate_file="$RUN_ROOT/empirical_${queue_bytes}q_${burst_bytes}burst_${rate_mbit}mbit.tsv"
  local current_cwnd="$start_cwnd"
  local probes=0
  local selected
  declare -A candidate_display=()
  declare -A candidate_throughput=()
  declare -A candidate_loss=()

  : > "$candidate_file"

  run_candidate() {
    local cwnd="$1"
    local run_output
    local display_cwnd throughput loss_rate row_count loss_rows first_loss avg_top result_dir server_log client_log

    if [[ -n "${candidate_loss[$cwnd]+set}" ]]; then
      return 0
    fi

    probes=$((probes + 1))
    if ! run_output="$(
      run_single "empirical" "$cwnd" "$rate_mbit" "$queue_bytes" "$burst_bytes" "$probes"
    )"; then
      return 1
    fi
    IFS=$'\t' read -r display_cwnd throughput loss_rate row_count loss_rows first_loss avg_top result_dir server_log client_log <<<"$run_output"
    candidate_display[$cwnd]="$display_cwnd"
    candidate_throughput[$cwnd]="$throughput"
    candidate_loss[$cwnd]="$loss_rate"
    printf '%s\t%s\t%s\t%s\n' "$cwnd" "$display_cwnd" "$throughput" "$loss_rate" >>"$candidate_file"
  }

  run_candidate "$current_cwnd"

  while ! float_le "${candidate_loss[$current_cwnd]}" "$EMPIRICAL_MAX_LOSS_RATE"; do
    (( current_cwnd <= 1 || probes >= EMPIRICAL_MAX_PROBES )) && break
    current_cwnd=$((current_cwnd - 1))
    run_candidate "$current_cwnd"
  done

  selected="$(
    python3 - "$candidate_file" "$EMPIRICAL_MAX_LOSS_RATE" <<'PY'
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
max_loss = float(sys.argv[2])
rows = []
with path.open("r", encoding="utf-8", newline="") as handle:
    for row in csv.reader(handle, delimiter="\t"):
        if len(row) != 4:
            continue
        cwnd, display, throughput, loss = row
        rows.append(
            {
                "cwnd": int(cwnd),
                "display": display,
                "throughput": float(throughput),
                "loss": float(loss),
            }
        )

acceptable = [row for row in rows if row["loss"] <= max_loss]
if acceptable:
    best = max(acceptable, key=lambda row: (row["throughput"], row["cwnd"]))
else:
    best = min(rows, key=lambda row: (row["loss"], -row["throughput"]))

print(f"{best['display']}\t{best['throughput']:.2f}\t{best['loss']:.6f}")
PY
  )"

  printf '%s\n' "$selected"
}

init_report() {
  mkdir -p "$RUN_ROOT/logs"
  {
    printf '# CWND Sweep Results\n\n'
    printf -- '- RTT: %s ms\n' "$RTT_MS"
    printf -- '- Size: %s GiB\n' "$SIZE_GIB"
    printf -- '- Server: %s:%s\n' "$SERVER_IP_FOR_CLIENT" "$SERVER_PORT"
    printf -- '- Client SSH host: %s:%s\n' "$(ssh_target)" "$CLIENT_SSH_PORT"
    printf -- '- Empirical max loss rate: %s\n\n' "$EMPIRICAL_MAX_LOSS_RATE"
    printf -- '- Empirical search: start at floored Reno average-top cwnd, then decrease until loss is acceptable\n\n'
  } >"$README_FILE"

  printf 'queue_bytes\tburst_bytes\trate_mbit\tmode\tconfigured_cwnd\tattempt\tdisplay_cwnd\tthroughput_mib_s\tloss_rate\trow_count\tloss_rows\tfirst_loss_cwnd\tavg_top_cwnd\tresult_dir\tserver_log\tclient_log\n' \
    >"$DETAILS_TSV"
}

main() {
  local queue_entry burst_entry rate_entry queue_bytes burst_bytes rate_mbit
  local bdp_cwnd bdp_plus_queue_cwnd
  local reno_display reno_tp reno_loss reno_first_loss reno_avg_top
  local bdp_display bdp_tp bdp_loss bdp_first_loss bdp_avg_top
  local bdpq_display bdpq_tp bdpq_loss bdpq_first_loss bdpq_avg_top
  local empirical_start empirical_display empirical_tp empirical_loss
  local reno_suffix fixed_suffix
  local reno_cell empirical_cell bdpq_cell bdp_cell
  local command_output

  need_command python3
  need_command sudo
  need_command ssh
  need_command setsid
  need_command stdbuf
  [[ -x "$RUN_SH" ]] || die "run.sh is not executable: $RUN_SH"
  [[ -f "$CALCULATION_PY" ]] || die "calculation.py not found: $CALCULATION_PY"
  check_client_ssh

  init_report
  refresh_sudo
  start_sudo_keepalive

  reno_suffix=""
  fixed_suffix=""
  (( RENO_RUNS > 1 )) && reno_suffix=" (${RENO_RUNS} runs)"
  (( FIXED_CWND_RUNS > 1 )) && fixed_suffix=" (${FIXED_CWND_RUNS} runs)"

  for queue_entry in "${QUEUE_SIZES[@]}"; do
    queue_bytes="$(number_token "$queue_entry" "QUEUE_SIZES")"

    for burst_entry in "${BURST_SIZES[@]}"; do
      burst_bytes="$(number_token "$burst_entry" "BURST_SIZES")"

      {
        printf '## Queue Size = %s bytes (burst: %s)\n\n' "$queue_bytes" "$burst_bytes"
        printf '| TGR | TCP Reno (avg top cwnd) | Empirical | BDP + Q_size - MSS | BDP |\n'
        printf '|---:|---:|---:|---:|---:|\n'
      } >>"$README_FILE"

      for rate_entry in "${TOKEN_GENERATION_RATES[@]}"; do
        rate_mbit="$(number_token "$rate_entry" "TOKEN_GENERATION_RATES")"

        if ! command_output="$(
          calculate_cwnds "$rate_mbit" "$queue_bytes"
        )"; then
          die "failed to calculate cwnd for rate=$rate_mbit queue=$queue_bytes"
        fi
        IFS=$'\t' read -r bdp_cwnd bdp_plus_queue_cwnd <<<"$command_output"

        if ! command_output="$(
          run_repeated "reno" "0" "$RENO_RUNS" "$rate_mbit" "$queue_bytes" "$burst_bytes"
        )"; then
          die "reno run failed for rate=$rate_mbit queue=$queue_bytes burst=$burst_bytes"
        fi
        IFS=$'\t' read -r reno_display reno_tp reno_loss reno_first_loss reno_avg_top <<<"$command_output"

        empirical_start="$(empirical_start_cwnd "$reno_avg_top" "$bdp_plus_queue_cwnd")"
        if ! command_output="$(
          empirical_search "$empirical_start" "$rate_mbit" "$queue_bytes" "$burst_bytes"
        )"; then
          die "empirical search failed for rate=$rate_mbit queue=$queue_bytes burst=$burst_bytes"
        fi
        IFS=$'\t' read -r empirical_display empirical_tp empirical_loss <<<"$command_output"

        if ! command_output="$(
          run_repeated "bdp_plus_queue" "$bdp_plus_queue_cwnd" "$FIXED_CWND_RUNS" "$rate_mbit" "$queue_bytes" "$burst_bytes"
        )"; then
          die "BDP+queue run failed for rate=$rate_mbit queue=$queue_bytes burst=$burst_bytes cwnd=$bdp_plus_queue_cwnd"
        fi
        IFS=$'\t' read -r bdpq_display bdpq_tp bdpq_loss bdpq_first_loss bdpq_avg_top <<<"$command_output"

        if ! command_output="$(
          run_repeated "bdp" "$bdp_cwnd" "$FIXED_CWND_RUNS" "$rate_mbit" "$queue_bytes" "$burst_bytes"
        )"; then
          die "BDP run failed for rate=$rate_mbit queue=$queue_bytes burst=$burst_bytes cwnd=$bdp_cwnd"
        fi
        IFS=$'\t' read -r bdp_display bdp_tp bdp_loss bdp_first_loss bdp_avg_top <<<"$command_output"

        reno_cell="$(format_cell "$reno_display" "$reno_tp" "$reno_suffix")"
        empirical_cell="$(format_cell "$empirical_display" "$empirical_tp")"
        bdpq_cell="$(format_cell "$bdpq_display" "$bdpq_tp" "$fixed_suffix")"
        bdp_cell="$(format_cell "$bdp_display" "$bdp_tp" "$fixed_suffix")"

        printf '| %s Mbit/s | %s | %s | %s | %s |\n' \
          "$rate_mbit" "$reno_cell" "$empirical_cell" "$bdpq_cell" "$bdp_cell" \
          >>"$README_FILE"

        log "updated report: $README_FILE"
      done

      printf '\n' >>"$README_FILE"
    done
  done

  log "done: $README_FILE"
  log "details: $DETAILS_TSV"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
