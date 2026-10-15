#!/bin/zsh --no-rcs
cat <<'JSON'
{"items":[
  {"title":"Install / Update CLI","subtitle":"Run uv sync in this workflow folder","arg":"install","uid":"install","valid":true},
  {"title":"Log In","subtitle":"Validate and save the SimpleLogin token in Keychain","arg":"login","uid":"login","valid":true},
  {"title":"Log Out","subtitle":"Remove the saved SimpleLogin token from Keychain","arg":"logout","uid":"logout","valid":true}
]}
JSON
