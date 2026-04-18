#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Ralph Wiggum Stop hook for the autosapien.com AI Employee.
#
# Invoked by Claude Code on the Stop event. It reads stdin JSON, decides if
# the current task is "done", and returns a JSON decision that either lets
# Claude exit or blocks the stop and feeds a continuation prompt back in.
#
# Two completion strategies, in order of precedence:
#   1. Promise-based: Claude's last message contains <promise>..._COMPLETE</promise>.
#   2. File-movement: every file originally in /Needs_Action has been moved
#      out (to /Plans, /Pending_Approval, /In_Progress, or /Done).
#
# The hook is self-limiting: it writes an iteration counter to .ralph_state
# and stops re-injecting after RALPH_MAX_ITERATIONS cycles — so a runaway
# loop cannot eat your API budget overnight.
# ---------------------------------------------------------------------------
set -eu

VAULT_PATH="${VAULT_PATH:-./AI_Employee_Vault}"
RALPH_MAX_ITERATIONS="${RALPH_MAX_ITERATIONS:-8}"
STATE_DIR="$VAULT_PATH/.ralph_state"
mkdir -p "$STATE_DIR"
ITER_FILE="$STATE_DIR/iter.count"
LAST_MSG_FILE="$STATE_DIR/last.msg"

# Read the hook input JSON from stdin (non-blocking).
INPUT="$(cat || true)"
echo "$INPUT" > "$STATE_DIR/last_input.json" 2>/dev/null || true

# ------------------------- 1. Promise-based completion ----------------------
# Claude Code places the last assistant message (plain text) in the hook input
# under .transcript or similar — but the contract varies by version, so we
# grep both stdin and a fallback transcript path.
PROMISE_REGEX='<promise>[A-Z_]*_COMPLETE</promise>'
if echo "$INPUT" | grep -Eq "$PROMISE_REGEX"; then
    echo '{"decision": "approve", "reason": "ralph.promise_seen"}'
    rm -f "$ITER_FILE"
    exit 0
fi

# ------------------------- 2. File-movement completion ----------------------
NEEDS_ACTION_COUNT="$(find "$VAULT_PATH/Needs_Action" -maxdepth 1 -type f -name '*.md' ! -name '.gitkeep' 2>/dev/null | wc -l | tr -d ' ')"
if [ "$NEEDS_ACTION_COUNT" = "0" ]; then
    echo '{"decision": "approve", "reason": "ralph.queue_empty"}'
    rm -f "$ITER_FILE"
    exit 0
fi

# ------------------------- 3. Iteration guard --------------------------------
ITER=0
if [ -f "$ITER_FILE" ]; then
    ITER="$(cat "$ITER_FILE")"
fi
ITER=$((ITER + 1))
echo "$ITER" > "$ITER_FILE"

if [ "$ITER" -ge "$RALPH_MAX_ITERATIONS" ]; then
    echo '{"decision": "approve", "reason": "ralph.max_iterations_hit"}'
    rm -f "$ITER_FILE"
    exit 0
fi

# ------------------------- 4. Re-inject prompt -------------------------------
# Block the stop and feed Claude a continuation prompt.
CONTINUATION="You still have $NEEDS_ACTION_COUNT file(s) in /Needs_Action. \
Ralph iteration $ITER/$RALPH_MAX_ITERATIONS. Continue the triage-inbox skill \
on the remaining items. End with <promise>TRIAGE_COMPLETE</promise> when the \
queue is empty or every remaining item is blocked on an external dependency."

# Emit the JSON decision that blocks stop and provides systemMessage.
printf '{"decision": "block", "reason": "ralph.still_working", "systemMessage": %s}\n' \
    "$(printf '%s' "$CONTINUATION" | python -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
