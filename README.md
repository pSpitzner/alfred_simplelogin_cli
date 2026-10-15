# SimpleLogin CLI

A small Python/Typer CLI for:

- listing all SimpleLogin aliases
- finding an alias by email/name
- listing contacts for an alias
- creating a contact/reverse alias for an alias
- printing the resulting `reverse_alias_address`

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## Authentication

Verify and save your SimpleLogin API key/PAT in the macOS Keychain with an
interactive, hidden-input prompt. `sl login` makes a lightweight aliases API
request first and only saves the token if the request succeeds:

```bash
sl login
```

Commands retrieve the saved token automatically. You can also set
`SIMPLELOGIN_API_KEY` or pass the global `--api-key` option; explicit values
and the environment variable take precedence over the Keychain. Avoid passing
secrets on the command line when possible, since they may be visible in shell
history or process listings.

The CLI sends the key as the `Authentication` HTTP header.

The default API base URL is:

```text
https://api.simplelogin.io
```

Override it with `SIMPLELOGIN_API_URL` if you use another SimpleLogin-compatible deployment.

## Commands

List aliases:

```bash
sl list-aliases
sl list-aliases --search github
```

Create a reverse alias:

```bash
sl create-reverse-alias github@aleeas.com person@example.com
```

or, if you know the numeric alias ID:

```bash
sl create-reverse-alias-by-id 123 person@example.com
```

The command prints the address to put in `To:` when sending mail from that alias.

List contacts:

```bash
sl list-contacts github@aleeas.com
```

Get raw JSON for scripting:

```bash
sl list-aliases --json
sl list-contacts github@aleeas.com --json
sl create-reverse-alias github@aleeas.com person@example.com --json
```

## Notes

SimpleLogin's API documents:

- `GET /api/v2/aliases?page_id=N`
- `GET /api/aliases/:alias_id/contacts?page_id=N`
- `POST /api/aliases/:alias_id/contacts`

The contacts endpoint returns `reverse_alias_address`. If the contact already exists, SimpleLogin may return it with `existed=true`, so the CLI treats that as success rather than creating a duplicate.

The CLI stores the PAT in the operating system's credential store through the
`keyring` library (the macOS Keychain on macOS); it does not write the PAT to a
project file.
