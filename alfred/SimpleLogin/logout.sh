#!/bin/zsh --no-rcs
set -u

CLI="${SIMPLELOGIN_CLI:-./.venv/bin/sl}"
if [[ ! -x "$CLI" ]]; then
  print -r -- "ERROR: SimpleLogin CLI not found. Run slsetup → Install / Update CLI."
  exit 1
fi

result="$("$CLI" logout 2>&1)"
exit_code=$?
if (( exit_code != 0 )); then
  print -r -- "ERROR: Could not log out: $result"
  exit 1
fi
print -r -- "$result"
