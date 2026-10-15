#!/bin/zsh --no-rcs
set -u

CLI="${SIMPLELOGIN_CLI:-./.venv/bin/sl}"
if [[ ! -x "$CLI" ]]; then
  CLI="$(command -v sl 2>/dev/null || true)"
fi
if [[ -z "$CLI" || ! -x "$CLI" ]]; then
  print -r -- '{"items":[{"title":"SimpleLogin CLI not found","subtitle":"Run slsetup → Install / Update CLI","valid":false}]}'
  exit 0
fi
PYTHON="${CLI%/*}/python"
if [[ ! -x "$PYTHON" ]]; then
  print -r -- '{"items":[{"title":"Python environment missing","subtitle":"Run slsetup → Install / Update CLI","valid":false}]}'
  exit 0
fi

unset SIMPLELOGIN_API_KEY
alias_id="${alias_id:-${1:-}}"
case "$alias_id" in
  ''|*[!0-9]*)
    print -r -- '{"items":[{"title":"No alias ID","subtitle":"Choose an alias first","valid":false}]}'
    exit 0
    ;;
esac

result="$("$CLI" list-contacts "$alias_id" --json 2>&1)"
exit_code=$?
if (( exit_code != 0 )); then
  printf '%s' "$result" | "$PYTHON" -c 'import json, sys; print(json.dumps({"items": [{"title": "SimpleLogin error", "subtitle": sys.stdin.read().strip(), "valid": False}]}))'
  exit 0
fi

printf '%s' "$result" | "$PYTHON" -c '
import json, sys
rows = json.load(sys.stdin)
items = []
for index, row in enumerate(rows):
    contact = str(row.get("contact") or "(unknown contact)")
    address = str(row.get("reverse_alias_address") or "")
    items.append({
        "title": contact,
        "subtitle": f"Reverse alias: {address}" if address else "No reverse alias created",
        "arg": address,
        "uid": str(row.get("id") or contact or index),
        "valid": bool(address),
    })
print(json.dumps({"items": items}, ensure_ascii=False))
'
