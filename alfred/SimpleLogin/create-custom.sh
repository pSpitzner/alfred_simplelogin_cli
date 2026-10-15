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

unset SIMPLELOGIN_API_KEY
prefix="${1:-}"
signed_suffix="${2:-}"
mailbox_id="${3:-}"
case "$mailbox_id" in
  ''|*[!0-9]*) print -r -- "No verified mailbox was selected."; exit 1 ;;
esac
if [[ -z "$prefix" || -z "$signed_suffix" ]]; then
  print -r -- "Enter an alias prefix and select a suffix."
  exit 1
fi

result="$("$CLI" alfred create-custom "$prefix" "$signed_suffix" "$mailbox_id" 2>&1)"
exit_code=$?
if (( exit_code != 0 )); then
  print -r -- "ERROR: Custom alias creation failed: $result"
  exit 1
fi

printf '%s' "$result" | /usr/bin/pbcopy
print -r -- "Custom alias created and copied: $result"
