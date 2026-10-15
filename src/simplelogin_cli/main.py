from __future__ import annotations

import json
import os
from typing import Any

import keyring
import typer

from .client import SimpleLoginClient, SimpleLoginError

KEYRING_SERVICE = "simplelogin-cli"
KEYRING_ACCOUNT = "simplelogin-api-key"

app = typer.Typer(
    name="sl",
    help="SimpleLogin alias/reverse-alias CLI.",
    no_args_is_help=True,
)


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


def print_json(value: Any) -> None:
    typer.echo(json.dumps(value, indent=2, ensure_ascii=False))


def alias_summary(alias: dict[str, Any]) -> str:
    alias_id = alias.get("id")
    email = alias.get("email", "")
    name = alias.get("name") or ""
    status = "enabled" if alias.get("enabled", True) else "disabled"
    if name:
        return f"{alias_id:>8}  {email:<45}  {status:<8}  {name}"
    return f"{alias_id:>8}  {email:<45}  {status}"


def resolve_alias(client: SimpleLoginClient, selector: str) -> dict[str, Any]:
    aliases = client.list_aliases()
    return client.find_alias(aliases, selector)


@app.callback()
def main(
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="SIMPLELOGIN_API_KEY",
        help="SimpleLogin PAT/API key. Prefer the environment variable.",
        hidden=True,
    ),
) -> None:
    """SimpleLogin alias/reverse-alias CLI."""
    # Keep this callback for Typer's global --api-key option.
    app.state_api_key = api_key  # type: ignore[attr-defined]


@app.command("login")
def login() -> None:
    """Save a SimpleLogin API token in the system keychain."""
    token = typer.prompt("SimpleLogin API token", hide_input=True).strip()
    if not token:
        raise typer.BadParameter("The API token cannot be empty.")

    client = get_client(token)
    try:
        client.verify_api_key()
    except SimpleLoginError as exc:
        raise typer.BadParameter(f"Could not verify API token: {exc}") from exc
    finally:
        client.close()

    keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, token)
    typer.echo("API token verified and saved to the system keychain.")


@app.command("list-aliases")
def aliases(
    search: str | None = typer.Option(
        None, "--search", "-s", help="Filter by email or name."
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Print raw JSON."
    ),
) -> None:
    """List all aliases."""
    client = get_client(getattr(app, "state_api_key", None))
    try:
        rows = client.list_aliases()
    except SimpleLoginError as exc:
        raise typer.ClickException(str(exc)) from exc
    finally:
        client.close()

    if search:
        q = search.casefold()
        rows = [
            a for a in rows
            if q in str(a.get("email", "")).casefold()
            or q in str(a.get("name") or "").casefold()
        ]

    if as_json:
        print_json(rows)
        return

    if not rows:
        typer.echo("No aliases found.")
        return

    typer.echo("      ID  Alias                                          Status    Name")
    typer.echo("--------  ---------------------------------------------  --------  --------------------")
    for alias in rows:
        typer.echo(alias_summary(alias))


@app.command("list-contacts")
def contacts(
    alias: str = typer.Argument(..., help="Alias ID, exact email, or name."),
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON."),
) -> None:
    """List contacts/reverse aliases belonging to an alias."""
    client = get_client(getattr(app, "state_api_key", None))
    try:
        resolved = resolve_alias(client, alias)
        rows = client.list_contacts(int(resolved["id"]))
    except (SimpleLoginError, KeyError, ValueError) as exc:
        raise typer.ClickException(str(exc)) from exc
    finally:
        client.close()

    if as_json:
        print_json(rows)
        return

    typer.echo(f"Alias: {resolved.get('email')} (id={resolved.get('id')})")
    if not rows:
        typer.echo("No contacts.")
        return

    for contact in rows:
        address = contact.get("reverse_alias_address") or "(no reverse alias address)"
        typer.echo(f"{contact.get('contact', '')}  ->  {address}")


def create_contact_for_alias(
    alias_selector: str,
    contact: str,
    as_json: bool,
) -> None:
    client = get_client(getattr(app, "state_api_key", None))
    try:
        resolved = resolve_alias(client, alias_selector)
        result = client.create_contact(int(resolved["id"]), contact)
    except (SimpleLoginError, KeyError, ValueError) as exc:
        raise typer.ClickException(str(exc)) from exc
    finally:
        client.close()

    if as_json:
        print_json(result)
        return

    address = result.get("reverse_alias_address")
    if not address:
        raise typer.ClickException(
            "SimpleLogin succeeded but did not return reverse_alias_address."
        )

    existed = result.get("existed", False)
    if existed:
        typer.echo("Existing reverse alias:")
    else:
        typer.echo("Created reverse alias:")

    typer.echo(address)


@app.command("create-reverse-alias")
def contact(
    alias: str = typer.Argument(..., help="Alias ID, exact email, or name."),
    contact_address: str = typer.Argument(
        ..., help="Recipient email address (or SimpleLogin contact string)."
    ),
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON."),
) -> None:
    """Create a contact and print its reverse-alias address."""
    create_contact_for_alias(alias, contact_address, as_json)


@app.command("create-reverse-alias-by-id")
def contact_id(
    alias_id: int = typer.Argument(..., help="SimpleLogin alias ID."),
    contact_address: str = typer.Argument(..., help="Recipient email address."),
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON."),
) -> None:
    """Create a contact using an alias ID without resolving the alias first."""
    client = get_client(getattr(app, "state_api_key", None))
    try:
        result = client.create_contact(alias_id, contact_address)
    except SimpleLoginError as exc:
        raise typer.ClickException(str(exc)) from exc
    finally:
        client.close()

    if as_json:
        print_json(result)
        return

    address = result.get("reverse_alias_address")
    if not address:
        raise typer.ClickException(
            "SimpleLogin succeeded but did not return reverse_alias_address."
        )

    typer.echo(address)


if __name__ == "__main__":
    app()
