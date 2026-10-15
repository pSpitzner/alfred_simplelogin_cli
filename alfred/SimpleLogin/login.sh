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

token="${login_token:-}"
unset login_token SIMPLELOGIN_API_KEY
if [[ -z "$token" ]]; then
  print -r -- "ERROR: Enter a SimpleLogin API token."
  exit 1
fi

result="$(printf '%s' "$token" | "$CLI" login --token-stdin 2>&1)"
exit_code=$?
unset token
if (( exit_code != 0 )); then
  print -r -- "ERROR: Log in failed: $result"
  exit 1
fi
print -r -- "Logged in: API token verified and saved in Keychain."
