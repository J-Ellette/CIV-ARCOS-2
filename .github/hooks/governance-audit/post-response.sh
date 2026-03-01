#!/usr/bin/env bash
set -euo pipefail

if [[ "${SKIP_GOVERNANCE_AUDIT:-}" == "true" ]]; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/audit.sh
source "$SCRIPT_DIR/lib/audit.sh"

append_event "$(jq -cn --arg ts "$(now_iso)" --arg level "$GOVERNANCE_LEVEL" '{timestamp:$ts,event:"response_completed",governance_level:$level}')"
