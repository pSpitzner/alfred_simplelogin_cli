#!/bin/zsh --no-rcs
set -u

CLI="${SIMPLELOGIN_CLI:-./.venv/bin/sl}"
if [[ ! -x "$CLI" ]]; then
  CLI="$(command -v sl 2>/dev/null || true)"
fi
if [[ -z "$CLI" || ! -x "$CLI" ]]; then
  print -r -- "ERROR: SimpleLogin CLI not found. Run slsetup → Install / Update CLI."
  exit 1
fi
PYTHON="${CLI%/*}/python"
if [[ ! -x "$PYTHON" ]]; then
  print -r -- "ERROR: Python environment missing. Run slsetup → Install / Update CLI."
  exit 1
fi

unset SIMPLELOGIN_API_KEY
alias_id="${1:-}"
recipient="${2:-}"
case "$alias_id" in
  ''|*[!0-9]*) print -r -- "No alias ID was passed from Alfred."; exit 1 ;;
esac
if [[ -z "$recipient" ]]; then
  print -r -- "Enter a recipient email address."
  exit 1
fi

result="$("$CLI" alfred create "$alias_id" "$recipient" --json 2>&1)"
exit_code=$?
if (( exit_code != 0 )); then
  print -r -- "ERROR: Reverse alias creation failed: $result"
  exit 1
fi

summary="$(printf '%s' "$result" | "$PYTHON" -c '
import json, subprocess, sys
try:
    result = json.load(sys.stdin)
except (json.JSONDecodeError, TypeError) as exc:
    print(f"ERROR: Invalid reverse-alias response: {exc}")
    raise SystemExit(1)
address = result.get("address")
if not address:
    print("ERROR: SimpleLogin returned no reverse-alias address")
    raise SystemExit(1)
subprocess.run(["/usr/bin/pbcopy"], input=address, text=True, check=True)
state = "Existing reverse alias copied" if result.get("existed") else "Reverse alias created and copied"
print(f"{state}: {address}")
')"
exit_code=$?
if (( exit_code != 0 )); then
  print -r -- "ERROR: Could not read reverse-alias result: $summary"
  exit 1
fi
print -r -- "$summary"
