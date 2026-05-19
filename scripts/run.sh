#!/usr/bin/env bash
# Heliograph runner — sources .env, runs the dispatcher, logs output.
# Invoked by cron (or any scheduler).
#
# DST-safe scheduling: cron fires this at both 11:00 and 12:00 UTC. The
# script then checks the current US/Eastern hour and only proceeds when
# it's 07. EDT → fires at 11 UTC. EST → fires at 12 UTC. Either way,
# exactly one daily send at 7 AM ET. Pass --force or set
# HELIOGRAPH_SKIP_TIME_CHECK=1 to bypass the gate (useful for manual runs).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

FORCE=0
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    *) ARGS+=("$arg") ;;
  esac
done

if [[ "$FORCE" -eq 0 && "${HELIOGRAPH_SKIP_TIME_CHECK:-0}" -eq 0 ]]; then
  ET_HOUR="$(TZ=America/New_York date +%H)"
  if [[ "$ET_HOUR" != "07" ]]; then
    # Quiet exit — keeps cron logs clean during the off-trigger hour.
    exit 0
  fi
fi

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

PYTHON_BIN="${HELIOGRAPH_PYTHON:-/home/ubuntu/miniconda3/bin/python}"

echo "==== $(date -Iseconds) heliograph starting (ET $(TZ=America/New_York date +%H:%M)) ===="
"$PYTHON_BIN" -m heliograph.main "${ARGS[@]+"${ARGS[@]}"}"
echo "==== $(date -Iseconds) heliograph done ===="
