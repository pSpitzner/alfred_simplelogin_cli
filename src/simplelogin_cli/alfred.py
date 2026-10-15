from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

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


@app.command("aliases")
def aliases(
    query: str = typer.Argument("", help="Filter aliases by email address."),
) -> None:
    """List aliases as Alfred Script Filter items, filtered by email only."""
    client = get_client(None)
    try:
        rows = client.list_aliases()
    except SimpleLoginError as exc:
        raise typer.BadParameter(str(exc)) from exc
    finally:
        client.close()

    query = query.strip().casefold()
    items = []
    for alias in rows:
        email = str(alias.get("email") or "")
        alias_id = alias.get("id")
        if not email or alias_id is None:
            continue
        if query and query not in email.casefold():
            continue
        items.append(
            {
                "title": email,
                "subtitle": alias_subtitle(alias),
                "arg": str(alias_id),
                "uid": str(alias_id),
                "valid": True,
            }
        )

    script_filter(items)


@app.command("create")
def create(
    alias_id: int = typer.Argument(..., help="SimpleLogin alias ID."),
    recipient: str = typer.Argument(..., help="Recipient email address."),
) -> None:
    """Create a reverse alias and print only its address for Alfred."""
    client = get_client(None)
    try:
        result = client.create_contact(alias_id, recipient)
    except SimpleLoginError as exc:
        raise typer.BadParameter(str(exc)) from exc
    finally:
        client.close()

    address = result.get("reverse_alias_address")
    if not address:
        raise typer.BadParameter(
            "SimpleLogin did not return a reverse-alias address."
        )
    typer.echo(address)
