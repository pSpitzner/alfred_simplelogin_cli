import json
from datetime import datetime, timezone

from simplelogin_cli import alfred


class FakeClient:
    def __init__(self, aliases=None, result=None):
        self.aliases = aliases or []
        self.result = result or {}
        self.closed = False

    def list_aliases(self):
        return self.aliases

    def create_contact(self, alias_id, recipient):
        self.created = (alias_id, recipient)
        return self.result

    def close(self):
        self.closed = True


def test_aliases_filters_by_email_and_emits_alfred_json(monkeypatch):
    activity_timestamp = datetime.now(timezone.utc).timestamp() - 2 * 3600
    client = FakeClient(
        aliases=[
            {
                "id": 1,
                "email": "work@example.com",
                "name": "Personal",
                "enabled": True,
                "latest_activity": {
                    "action": "forward",
                    "timestamp": activity_timestamp,
                },
            },
            {"id": 2, "email": "personal@example.com", "name": "Work"},
        ]
    )
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.aliases("WORK")

    assert json.loads(output[0]) == {
        "items": [
            {
                "title": "work@example.com",
                "subtitle": "Enabled · Last forwarded 2 hours ago",
                "arg": "1",
                "uid": "1",
                "valid": True,
            }
        ]
    }
    assert client.closed


def test_aliases_without_query_returns_all_emails(monkeypatch):
    client = FakeClient(
        aliases=[
            {"id": 1, "email": "first@example.com"},
            {"id": 2, "email": "second@example.com"},
        ]
    )
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.aliases("")

    assert [item["title"] for item in json.loads(output[0])["items"]] == [
        "first@example.com",
        "second@example.com",
    ]


def test_alias_subtitle_shows_disabled_pinned_and_no_activity():
    assert alfred.alias_subtitle(
        {"enabled": False, "pinned": True},
        now=datetime(2025, 1, 1, tzinfo=timezone.utc),
    ) == "Disabled · Pinned · No activity recorded"


def test_alias_subtitle_formats_latest_reply_time():
    now = datetime(2025, 1, 3, tzinfo=timezone.utc)
    timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp()

    assert alfred.alias_subtitle(
        {
            "enabled": True,
            "latest_activity": {"action": "reply", "timestamp": timestamp},
        },
        now=now,
    ) == "Enabled · Last replied 2 days ago"


def test_create_prints_only_reverse_alias_address(monkeypatch):
    client = FakeClient(result={"reverse_alias_address": "reverse@example.com"})
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.create(123, "person@example.com")

    assert client.created == (123, "person@example.com")
    assert output == ["reverse@example.com"]
    assert client.closed
