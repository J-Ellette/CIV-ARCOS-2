#!/usr/bin/env bash
set -euo pipefail

if [[ "${SKIP_GOVERNANCE_AUDIT:-}" == "true" ]]; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/audit.sh
source "$SCRIPT_DIR/lib/audit.sh"

input=""
if [[ $# -gt 0 ]]; then
  input="$*"
elif ! [ -t 0 ]; then
  input="$(cat)"
fi

if [[ -z "$input" ]]; then
  append_event "$(jq -cn --arg ts "$(now_iso)" --arg level "$GOVERNANCE_LEVEL" '{timestamp:$ts,event:"prompt_scanned",governance_level:$level,status:"empty"}')"
  exit 0
fi

threats="$(detect_threats "$input")"
threat_count="$(jq 'length' <<<"$threats")"

if [[ "$threat_count" -gt 0 ]]; then
  append_event "$(jq -cn --arg ts "$(now_iso)" --arg level "$GOVERNANCE_LEVEL" --argjson count "$threat_count" --argjson threats "$threats" '{timestamp:$ts,event:"threat_detected",governance_level:$level,threat_count:$count,threats:$threats}')"
  if should_block "$threat_count"; then
    echo "Governance audit blocked prompt: detected $threat_count potential threat pattern(s)." >&2
    exit 2
  fi
else
  append_event "$(jq -cn --arg ts "$(now_iso)" --arg level "$GOVERNANCE_LEVEL" '{timestamp:$ts,event:"prompt_scanned",governance_level:$level,status:"clean"}')"
fi
