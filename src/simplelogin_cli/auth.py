from __future__ import annotations

import os

import keyring
import typer

from .client import SimpleLoginClient

KEYRING_SERVICE = "simplelogin-cli"
KEYRING_ACCOUNT = "simplelogin-api-key"


def get_api_key(explicit: str | None) -> str:
    key = explicit or os.getenv("SIMPLELOGIN_API_KEY")
    if not key:
        key = keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
    if not key:
        raise typer.BadParameter(
            "No API key. Run `sl login`, set SIMPLELOGIN_API_KEY, or use --api-key."
        )
    return key.strip()


def get_client(api_key: str | None) -> SimpleLoginClient:
    return SimpleLoginClient(
        api_key=get_api_key(api_key),
        base_url=os.getenv(
            "SIMPLELOGIN_API_URL",
            "https://api.simplelogin.io",
        ),
    )
