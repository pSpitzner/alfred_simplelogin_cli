#!/bin/zsh --no-rcs
set -u

uv_bin="${UV:-}"
if [[ -z "$uv_bin" ]]; then
  uv_bin="$(command -v uv 2>/dev/null || true)"
fi
if [[ -z "$uv_bin" ]]; then
  for candidate in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv" /opt/homebrew/bin/uv /usr/local/bin/uv; do
    if [[ -x "$candidate" ]]; then
      uv_bin="$candidate"
      break
    fi
  done
fi
if [[ "$uv_bin" != */* ]]; then
  uv_bin="$(command -v "$uv_bin" 2>/dev/null || true)"
fi

if [[ -z "$uv_bin" || ! -x "$uv_bin" ]]; then
  print -r -- "ERROR: Set the UV workflow variable to the full path of uv, then run Install / Update CLI again."
  exit 1
fi

project_dir="$PWD"
output="$("$uv_bin" sync --locked --project "$project_dir" 2>&1)"
exit_code=$?
if (( exit_code != 0 )); then
  summary="$(printf '%s\n' "$output" | awk 'NF { last = $0 } END { print last }')"
  print -r -- "ERROR: uv sync failed: $summary"
  exit 1
fi

cli="${SIMPLELOGIN_CLI:-./.venv/bin/sl}"
if [[ ! -x "$cli" ]]; then
  print -r -- "ERROR: uv sync finished, but the CLI was not found at $cli. Check SIMPLELOGIN_CLI."
  exit 1
fi
print -r -- "Installed dependencies. SimpleLogin CLI is ready at $cli."
