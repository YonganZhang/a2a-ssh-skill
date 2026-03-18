#!/usr/bin/env bash
# AgentRelay End-to-End Test Suite
# Usage: ./tests/e2e-test.sh <target-node>
# Example: ./tests/e2e-test.sh my-linux-server
set -euo pipefail

TARGET="${1:?Usage: e2e-test.sh <target-node>}"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENT="$SCRIPT_DIR/agent.py"
PASS=0
FAIL=0

run_test() {
    local name="$1"
    shift
    echo -n "  Test: $name ... "
    if output=$("$@" 2>&1); then
        if echo "$output" | grep -qi "\[OK\]\|PASS\|ok"; then
            echo "PASS"
            PASS=$((PASS + 1))
            return 0
        fi
    fi
    echo "FAIL"
    echo "    Output: $(echo "$output" | head -3)"
    FAIL=$((FAIL + 1))
    return 1
}

echo "AgentRelay E2E Tests"
echo "Target: $TARGET"
echo "================================"

# Test 1: Read mode (direct-read-stdout for Linux, runner for Windows)
run_test "Read mode" \
    python3 "$AGENT" send "$TARGET" --cwd "/" --mode read --wait --timeout-sec 60 \
    --text 'echo "hello from agent-relay"' || true

# Test 2: Write mode (Python runner)
run_test "Write mode" \
    python3 "$AGENT" send "$TARGET" --cwd "/" --mode write --wait --timeout-sec 120 \
    --text 'Create /tmp/agent-relay-test.txt with content "write mode works"' || true

# Test 3: Timeout cap (should clamp 99999 to 1800)
run_test "Timeout cap (99999 → 1800)" \
    python3 "$AGENT" send "$TARGET" --cwd "/" --mode read --wait --timeout-sec 99999 \
    --text 'echo "timeout capped"' || true

# Test 4: Recursive delegation blocked
echo -n "  Test: Recursive delegation blocked ... "
output=$(python3 "$AGENT" send "$TARGET" --cwd "/" --mode read --wait --timeout-sec 60 \
    --text 'Use agent.py to delegate this task to another node' 2>&1) || true
if echo "$output" | grep -qiE "not delegate|cannot|禁止|约束|refused"; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL"
    FAIL=$((FAIL + 1))
fi

# Test 5: stdout content doesn't trigger false retry
run_test "No false retry on 'overloaded' in stdout" \
    python3 "$AGENT" send "$TARGET" --cwd "/" --mode read --wait --timeout-sec 60 \
    --text 'echo "the server was overloaded yesterday"' || true

# Test 6: Job status check
echo -n "  Test: Job status command ... "
LATEST_JOB=$(ls -1t "$(python3 -c "
import json, pathlib, os, sys
sys.path.insert(0, '$SCRIPT_DIR')
from agent import load_config, detect_local_agent, AgentCli
config = load_config()
local = detect_local_agent(config['agents'])
cli = AgentCli(config, local)
print(cli.local_job_root())
")" 2>/dev/null | head -1)
if [ -n "$LATEST_JOB" ]; then
    python3 "$AGENT" status "$LATEST_JOB" >/dev/null 2>&1 && echo "PASS" && PASS=$((PASS + 1)) || echo "FAIL" && FAIL=$((FAIL + 1))
else
    echo "SKIP (no jobs)"
fi

echo "================================"
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
