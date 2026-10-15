# SimpleLogin Alfred Workflow

## Install and configure

1. Import `SimpleLogin.alfredworkflow` into Alfred.
2. Set the workflow's `UV` variable to the full path of your `uv` executable.
   `SIMPLELOGIN_CLI` defaults to `./.venv/bin/sl` in the deployed workflow.
3. Type `slsetup` and select **Install / Update CLI**. This runs
   `uv sync --locked` in the workflow folder and creates its `.venv` there.
4. Type `slsetup` and select **Log In**. Alfred opens a blank text input for
   the token, verifies it, and saves it in Keychain. The token is visible while
   entered and may be retained in Alfred's search history; use this option only
   if you are comfortable entering the secret in Alfred. Select **Log Out** to
   remove it from Keychain.

## Use

- **`sl`**: Fuzzy-search aliases by email, name, or note. **⌘C** copies the
  selected alias's email (not its internal ID). Return opens a blank Alfred
  input for the recipient email and creates/copies the reverse alias.
  **⌥Return** instead opens existing contacts/reverse aliases.
- **`slc`**: Search aliases, then browse their contacts/reverse aliases. Select
  a reverse-alias address to copy it.
- **`slnew`**: Choose an available suffix. Alfred keeps the signed suffix and
  mailbox as workflow variables, then opens a blank follow-up input for the
  alias prefix. Return creates a custom alias using the default verified mailbox.
- **`slsetup`**: Choose Install / Update, Log In, or Log Out.

The workflow folder contains `pyproject.toml`, `uv.lock`, and `src/`; it is the
project root for `uv sync`. The two configurable environment variables are
`UV` and `SIMPLELOGIN_CLI`. The login action passes the token to the CLI over
stdin and clears its workflow variable after submission. Errors after actions
produce a notification and an Alfred Large Type message. The workflow unsets
any inherited `SIMPLELOGIN_API_KEY` so API calls use the Keychain credential.
