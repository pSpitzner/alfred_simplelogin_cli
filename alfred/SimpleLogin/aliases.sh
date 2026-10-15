#!/bin/zsh --no-rcs
set -u

CLI="${SIMPLELOGIN_CLI:-./.venv/bin/sl}"
if [[ ! -x "$CLI" ]]; then
  CLI="$(command -v sl 2>/dev/null || true)"
fi

if [[ -z "$CLI" || ! -x "$CLI" ]]; then
  print -r -- '{"items":[{"title":"SimpleLogin CLI not found","subtitle":"Install the project or set SIMPLELOGIN_CLI to its executable","valid":false}]}'
  exit 0
fi
PYTHON="${CLI%/*}/python"
if [[ ! -x "$PYTHON" ]]; then
  print -r -- '{"items":[{"title":"Python environment missing","subtitle":"Run slsetup → Install / Update CLI","valid":false}]}'
  exit 0
fi

# Alfred should use the credential saved with `sl login`, not a stale shell token.
unset SIMPLELOGIN_API_KEY
result="$("$CLI" alfred aliases "${1:-}" 2>&1)"
exit_code=$?
if (( exit_code != 0 )); then
  printf '%s' "$result" | "$PYTHON" -c 'import json, sys; print(json.dumps({"items": [{"title": "SimpleLogin error", "subtitle": sys.stdin.read().strip(), "valid": False}]}))'
  exit 0
fi

printf '%s\n' "$result"
