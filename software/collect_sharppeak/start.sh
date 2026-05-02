#!/usr/bin/env bash
set -euo pipefail

SECOND_SCRIPT="run_collect_sharppeak.py"
FIRST_SCRIPT="collect-test.py"

DELAY_SECONDS=3

# Start second program first
# > log2.txt 2>&1 
python3 "$SECOND_SCRIPT" &
second_pid=$!

sleep "$DELAY_SECONDS"

python3 "$FIRST_SCRIPT"
first_status=$?

# Stop second program after first program exits
wait "$second_pid" 2>/dev/null || true

exit "$first_status"
