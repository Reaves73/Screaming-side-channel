#!/usr/bin/env bash
set -euo pipefail

SECOND_SCRIPT="run_collect_sharppeak.py"
FIRST_SCRIPT="collect-test.py"

DELAY_SECONDS=3

# Start second program first
python3 "$SECOND_SCRIPT" > log2.txt 2>&1 &
second_pid=$!

# Ensure second program is stopped if this script exits early
cleanup() {
  if kill -0 "$second_pid" 2>/dev/null; then
    kill "$second_pid"
    wait "$second_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# Delay before starting first program
sleep "$DELAY_SECONDS"

# Start first program and wait until it ends
python3 "$FIRST_SCRIPT"
first_status=$?

# Stop second program after first program exits
kill "$second_pid" 2>/dev/null || true
wait "$second_pid" 2>/dev/null || true

exit "$first_status"
