from __future__ import annotations

import json
import os
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn

import typer

from .auth import get_client
from .client import SimpleLoginError

app = typer.Typer(
    name="alfred",
    help="Commands for Alfred workflows.",
    no_args_is_help=True,
)


def script_filter(items: list[dict[str, Any]]) -> None:
    """Write Alfred Script Filter JSON to stdout."""
    typer.echo(json.dumps({"items": items}, ensure_ascii=False))


def raise_cli_error(message: str) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)


def relative_time(value: Any, now: datetime | None = None) -> str | None:
    try:
        if isinstance(value, (int, float)):
            timestamp = float(value)
            if abs(timestamp) >= 100_000_000_000:
                timestamp /= 1000
            activity_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif isinstance(value, str):
            activity_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if activity_at.tzinfo is None:
                activity_at = activity_at.replace(tzinfo=timezone.utc)
            else:
                activity_at = activity_at.astimezone(timezone.utc)
        else:
            return None
    except (OverflowError, OSError, TypeError, ValueError):
        return None

    current_time = now or datetime.now(timezone.utc)
    seconds = (current_time - activity_at).total_seconds()
    future = seconds < 0
    seconds = abs(seconds)
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        amount, unit = int(seconds // 60), "minute"
    elif seconds < 86400:
        amount, unit = int(seconds // 3600), "hour"
    elif seconds < 7 * 86400:
        amount, unit = int(seconds // 86400), "day"
    elif seconds < 30 * 86400:
        amount, unit = int(seconds // (7 * 86400)), "week"
    elif seconds < 365 * 86400:
        amount, unit = int(seconds // (30 * 86400)), "month"
    else:
        amount, unit = int(seconds // (365 * 86400)), "year"

    label = f"{amount} {unit}{'' if amount == 1 else 's'}"
    return f"in {label}" if future else f"{label} ago"


def alias_subtitle(
    alias: dict[str, Any], now: datetime | None = None
) -> str:
    details = ["Enabled" if alias.get("enabled", True) else "Disabled"]
    if alias.get("pinned"):
        details.append("Pinned")

    activity = alias.get("latest_activity")
    if isinstance(activity, dict):
        action = str(activity.get("action") or "activity").casefold()
        action_label = {
            "forward": "forwarded",
            "reply": "replied",
            "block": "blocked",
            "bounced": "bounced",
        }.get(action, action)
        when = relative_time(activity.get("timestamp"), now)
        latest = f"Last {action_label}"
        if when:
            latest = f"{latest} {when}"
    else:
        latest = "No activity recorded"
    details.append(latest)
    return " · ".join(details)


def normalize_search_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def fuzzy_text_score(needle: str, haystack: str) -> float | None:
    """Score a case/accent-insensitive subsequence match; lower is better."""
    if needle in haystack:
        return haystack.index(needle) / 100

    positions = []
    cursor = 0
    for character in needle:
        position = haystack.find(character, cursor)
        if position < 0:
            return None
        positions.append(position)
        cursor = position + 1

    span = positions[-1] - positions[0] + 1
    gaps = span - len(needle)
    return gaps + positions[0] / 100 + len(haystack) / 100_000


def alias_search_score(alias: dict[str, Any], query: str) -> float | None:
    terms = normalize_search_text(query).split()
    if not terms:
        return 0
    fields = [
        normalize_search_text(str(alias.get(field) or ""))
        for field in ("email", "name", "note")
    ]
    score = 0.0
    for term in terms:
        matches = [
            field_score
            for field in fields
            if (field_score := fuzzy_text_score(term, field)) is not None
        ]
        if not matches:
            return None
        score += min(matches)
    return score


def cached_aliases() -> list[dict[str, Any]]:
    cache_dir = Path(
        os.environ.get("alfred_workflow_cache")
        or (Path.home() / ".cache" / "simplelogin-cli")
    )
    cache_file = cache_dir / "aliases.json"
    try:
        if time.time() - cache_file.stat().st_mtime < 20:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(cached, list):
                return cached
    except (OSError, ValueError):
        pass

    client = get_client(None)
    try:
        rows = client.list_aliases()
    finally:
        client.close()

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        temp_file = cache_file.with_name(f"aliases.{os.getpid()}.tmp")
        temp_file.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        temp_file.replace(cache_file)
    except OSError:
        pass
    return rows


@app.command("aliases")
def aliases(
    query: str = typer.Argument("", help="Fuzzy-filter aliases by email or name."),
) -> None:
    """Return aliases fuzzy-matched by email, name, or note."""
    try:
        rows = cached_aliases()
    except SimpleLoginError as exc:
        raise typer.BadParameter(str(exc)) from exc

    matches = []
    for index, alias in enumerate(rows):
        email = str(alias.get("email") or "")
        alias_id = alias.get("id")
        score = alias_search_score(alias, query)
        if not email or alias_id is None or score is None:
            continue
        matches.append((score, index, alias))
    if query.strip():
        matches.sort(key=lambda match: (match[0], match[1]))

    items = []
    for _, _, alias in matches:
        email = str(alias.get("email") or "")
        alias_id = alias.get("id")
        items.append(
            {
                "title": email,
                "subtitle": alias_subtitle(alias),
                "match": " ".join(
                    part for part in (
                        email,
                        str(alias.get("name") or ""),
                        str(alias.get("note") or ""),
                    ) if part
                ),
                "arg": email,
                "uid": str(alias_id),
                "variables": {
                    "alias_id": str(alias_id),
                    "alias_email": email,
                },
                "mods": {
                    "alt": {
                        "valid": True,
                        "arg": str(alias_id),
                        "subtitle": "View existing reverse aliases",
                        "variables": {
                            "alias_id": str(alias_id),
                            "alias_email": email,
                        },
                    }
                },
                "valid": True,
            }
        )

    script_filter(items)


@app.command("new-aliases")
def new_aliases(
    query: str = typer.Argument("", help="Filter available alias suffixes."),
) -> None:
    """Show custom-alias suffixes as Alfred Script Filter items."""
    client = get_client(None)
    try:
        options = client.list_alias_options()
        mailboxes = client.list_mailboxes()
    except SimpleLoginError as exc:
        raise typer.BadParameter(str(exc)) from exc
    finally:
        client.close()

    if not options.get("can_create", True):
        script_filter(
            [{
                "title": "Custom aliases are unavailable",
                "subtitle": "SimpleLogin does not allow creating aliases for this account",
                "valid": False,
            }]
        )
        return

    available_mailboxes = [mailbox for mailbox in mailboxes if mailbox.get("verified")]
    mailbox = next(
        (item for item in available_mailboxes if item.get("default")),
        available_mailboxes[0] if available_mailboxes else None,
    )
    if mailbox is None:
        script_filter(
            [{
                "title": "No verified mailbox",
                "subtitle": "Verify a mailbox in SimpleLogin before creating an alias",
                "valid": False,
            }]
        )
        return

    prefix = str(options.get("prefix_suggestion") or "")
    query = query.strip().casefold()
    items = []
    for suffix in options.get("suffixes") or []:
        label = str(suffix.get("suffix") or "")
        signed_suffix = suffix.get("signed_suffix")
        if not label or not signed_suffix:
            continue
        if query and query not in label.casefold():
            continue
        suggested_address = f"{prefix}{label}"
        suffix_type = "Premium suffix" if suffix.get("is_premium") else "Alias suffix"
        items.append(
            {
                "title": suggested_address or label,
                "subtitle": f"{suffix_type} · sends to {mailbox.get('email', '')}",
                "arg": str(signed_suffix),
                "uid": label,
                "variables": {
                    "mailbox_id": str(mailbox["id"]),
                    "prefix_suggestion": prefix,
                    "alias_suffix": label,
                    "signed_suffix": str(signed_suffix),
                },
                "valid": True,
            }
        )

    script_filter(items)


@app.command("create-custom")
def create_custom(
    prefix: str = typer.Argument(..., help="Custom alias prefix."),
    signed_suffix: str = typer.Argument(..., help="Opaque suffix from SimpleLogin."),
    mailbox_id: int = typer.Argument(..., help="Verified mailbox ID."),
) -> None:
    """Create a custom alias and print its address for Alfred."""
    client = get_client(None)
    try:
        result = client.create_custom_alias(prefix, signed_suffix, [mailbox_id])
    except SimpleLoginError as exc:
        raise_cli_error(str(exc))
    finally:
        client.close()

    address = result.get("email")
    if not address:
        raise_cli_error("SimpleLogin did not return the created alias address.")
    typer.echo(address)


@app.command("create")
def create(
    alias_id: int = typer.Argument(..., help="SimpleLogin alias ID."),
    recipient: str = typer.Argument(..., help="Recipient email address."),
    as_json: bool = typer.Option(False, "--json", hidden=True),
) -> None:
    """Create a reverse alias and print only its address for Alfred."""
    client = get_client(None)
    try:
        result = client.create_contact(alias_id, recipient)
    except SimpleLoginError as exc:
        raise_cli_error(str(exc))
    finally:
        client.close()

    address = result.get("reverse_alias_address")
    if not address:
        raise_cli_error(
            "SimpleLogin did not return a reverse-alias address."
        )
    if as_json is True:
        typer.echo(
            json.dumps(
                {"address": address, "existed": bool(result.get("existed", False))},
                ensure_ascii=False,
            )
        )
    else:
        typer.echo(address)
