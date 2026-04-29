#!/usr/bin/env bash
set -euo pipefail

MODULE_NAME="my_cca"
MODULE_FILE="${MODULE_NAME}.ko"
SIGN_KEY="${HOME}/module-signing/MOK.priv"
SIGN_CERT="${HOME}/module-signing/MOK.der"
SIGN_FILE="/usr/src/linux-headers-$(uname -r)/scripts/sign-file"

cd "$(dirname "$0")"

log() {
  printf '\n==> %s\n' "$*"
}

need_file() {
  if [[ ! -f "$1" ]]; then
    printf 'Error: required file not found: %s\n' "$1" >&2
    exit 1
  fi
}

# I think we only need password once when running the top "bash" script
log "Checking sudo access"
echo "This script may ask for your sudo password to sign, unload, and load the kernel module."
sudo -v

# Keep the sudo session alive until the script finishes to avoid multiple password prompts
keep_sudo_alive() {
  while true; do
    sudo -n true
    sleep 60
    kill -0 "$$" || exit
  done 2>/dev/null
}
keep_sudo_alive &
SUDO_KEEPALIVE_PID=$!
trap 'kill "$SUDO_KEEPALIVE_PID" 2>/dev/null || true' EXIT

log "Building ${MODULE_NAME}"
make

need_file "$MODULE_FILE"
need_file "$SIGN_FILE"
need_file "$SIGN_KEY"
need_file "$SIGN_CERT"

log "Signing ${MODULE_FILE}"
sudo "$SIGN_FILE" sha256 "$SIGN_KEY" "$SIGN_CERT" "$MODULE_FILE"

log "Checking whether ${MODULE_NAME} is already loaded"
if sudo lsmod | grep -q "^${MODULE_NAME}[[:space:]]"; then
  log "Unloading existing ${MODULE_NAME}"
  sudo rmmod "$MODULE_NAME"
else
  echo "${MODULE_NAME} is not currently loaded."
fi

log "Loading ${MODULE_FILE}"
sudo insmod "$MODULE_FILE"

log "Verifying TCP congestion control list"
sysctl net.ipv4.tcp_allowed_congestion_control

if sysctl -n net.ipv4.tcp_allowed_congestion_control | grep -qw "$MODULE_NAME"; then
  printf '\nSuccess: %s is loaded and available to the TCP stack.\n' "$MODULE_NAME"
else
  printf '\nWarning: %s was inserted, but it was not found in tcp_allowed_congestion_control.\n' "$MODULE_NAME" >&2
  exit 1
fi

# FIXME; run a short script that sets the limit of my_cca.c