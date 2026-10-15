# SimpleLogin CLI

A small CLI for managing SimpleLogin aliases and reverse aliases.

100% vibe coded.

## Setup

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync
uv run sl login
```

Login verifies your API key and saves it in the Keychain. You can also
set `SIMPLELOGIN_API_KEY` to use an environment-provided key. Run
`uv run sl logout` to remove the saved Keychain key.

## Usage

```bash
# List and search aliases
uv run sl list-aliases
uv run sl list-aliases --search github

# List an alias's contacts and reverse aliases
uv run sl list-contacts github@aleeas.com

# Create a reverse alias for a recipient
uv run sl create-reverse-alias github@aleeas.com person@example.com

# Get JSON for scripting
uv run sl list-aliases --json
```

Creating a reverse alias for an existing contact reuses its current address.

## Alfred Workflow

Grab the release from Github and see the
[Alfred workflow guide](alfred/SimpleLogin/README.md) for installation and usage.
