#!/usr/bin/env bash
set -euo pipefail

if [[ "${SKIP_LOGGING:-}" == "true" ]]; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/log.sh
source "$SCRIPT_DIR/lib/log.sh"

size=0
if [[ $# -gt 0 ]]; then
  size=${#*}
elif ! [ -t 0 ]; then
  payload="$(cat)"
  size=${#payload}
fi

prompt_event "$size"
