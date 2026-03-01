#!/usr/bin/env bash
set -euo pipefail

AUDIT_LOG="${AUDIT_LOG:-logs/copilot/governance/audit.log}"
GOVERNANCE_LEVEL="${GOVERNANCE_LEVEL:-standard}"
BLOCK_ON_THREAT="${BLOCK_ON_THREAT:-false}"

mkdir -p "$(dirname "$AUDIT_LOG")"

now_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

append_event() {
  local payload="$1"
  printf '%s\n' "$payload" >> "$AUDIT_LOG"
}

detect_threats() {
  local input="$1"
  local threats="[]"

  add_threat() {
    local category="$1"
    local severity="$2"
    local description="$3"
    local evidence="$4"
    threats="$(jq -c --arg c "$category" --argjson s "$severity" --arg d "$description" --arg e "$evidence" '. + [{category:$c,severity:$s,description:$d,evidence:$e}]' <<<"$threats")"
  }

  if grep -Eiq '(curl|wget).*(http|https)://.*(dump|all|database|secret|token)' <<<"$input"; then
    add_threat "data_exfiltration" 0.90 "Potential data exfiltration pattern" "curl/wget external exfiltration pattern"
  fi
  if grep -Eiq '\bsudo\b|chmod\s+777|/etc/sudoers|Set-ExecutionPolicy\s+Bypass' <<<"$input"; then
    add_threat "privilege_escalation" 0.85 "Potential privilege escalation command" "sudo/chmod/sudoers pattern"
  fi
  if grep -Eiq 'rm\s+-rf\s+/|drop\s+database|truncate\s+table\s+.*;' <<<"$input"; then
    add_threat "system_destruction" 0.95 "Potential destructive operation" "rm -rf or drop/truncate pattern"
  fi
  if grep -Eiq 'ignore\s+previous\s+instructions|system\s+prompt|developer\s+message' <<<"$input"; then
    add_threat "prompt_injection" 0.70 "Potential prompt injection phrase" "instruction override pattern"
  fi
  if grep -Eiq 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{20,}' <<<"$input"; then
    add_threat "credential_exposure" 0.95 "Potential secret credential pattern" "access key/token pattern"
  fi

  printf '%s\n' "$threats"
}

should_block() {
  local threat_count="$1"
  if [[ "$threat_count" -eq 0 ]]; then
    return 1
  fi
  case "$GOVERNANCE_LEVEL" in
    strict|locked)
      return 0
      ;;
    standard)
      [[ "${BLOCK_ON_THREAT,,}" == "true" ]]
      return
      ;;
    open)
      return 1
      ;;
    *)
      return 1
      ;;
  esac
}
