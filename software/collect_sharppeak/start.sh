#!/usr/bin/env bash
set -euo pipefail

SECOND_SCRIPT="run_collect_sharppeak.py"
FIRST_SCRIPT="collect-test.py"

DELAY_SECONDS=3

# Start second program first
python3 "$SECOND_SCRIPT" > log2.txt 2>&1 &
second_pid=$!

sleep "$DELAY_SECONDS"

python3 "$FIRST_SCRIPT"
first_status=$?

# Stop second program after first program exits
wait "$second_pid" 2>/dev/null || true

exit "$first_status"
