#!/usr/bin/env bash
set -euo pipefail

SESSION_LOG="${SESSION_LOG:-logs/copilot/session.log}"
PROMPT_LOG="${PROMPT_LOG:-logs/copilot/prompts.log}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

mkdir -p "$(dirname "$SESSION_LOG")"
mkdir -p "$(dirname "$PROMPT_LOG")"

now_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

session_event() {
  local event="$1"
  printf '%s\n' "$(jq -cn --arg ts "$(now_iso)" --arg ev "$event" --arg cwd "$(pwd)" --arg level "$LOG_LEVEL" '{timestamp:$ts,event:$ev,cwd:$cwd,log_level:$level}')" >> "$SESSION_LOG"
}

prompt_event() {
  local size="$1"
  printf '%s\n' "$(jq -cn --arg ts "$(now_iso)" --arg ev "promptSubmit" --arg cwd "$(pwd)" --argjson bytes "$size" '{timestamp:$ts,event:$ev,cwd:$cwd,prompt_bytes:$bytes}')" >> "$PROMPT_LOG"
}
