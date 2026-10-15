import json
from datetime import datetime, timezone

import pytest

from simplelogin_cli import alfred


class FakeClient:
    def __init__(self, aliases=None, result=None):
        self.aliases = aliases or []
        self.result = result or {}
        self.closed = False
        self.list_calls = 0

    def list_aliases(self):
        self.list_calls += 1
        return self.aliases

    def create_contact(self, alias_id, recipient):
        self.created = (alias_id, recipient)
        return self.result

    def close(self):
        self.closed = True


def test_aliases_returns_all_searchable_fields_for_alfred(monkeypatch, tmp_path):
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
    monkeypatch.setenv("alfred_workflow_cache", str(tmp_path))
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.aliases("WORK")

    items = json.loads(output[0])["items"]
    assert [item["title"] for item in items] == [
        "work@example.com",
        "personal@example.com",
    ]
    assert [item["match"] for item in items] == [
        "work@example.com Personal",
        "personal@example.com Work",
    ]
    assert items[0]["subtitle"] == "Enabled · Last forwarded 2 hours ago"
    assert items[0]["arg"] == "work@example.com"
    assert items[0]["mods"]["alt"]["arg"] == "1"
    assert client.closed


def test_aliases_without_query_returns_all_emails(monkeypatch, tmp_path):
    client = FakeClient(
        aliases=[
            {"id": 1, "email": "first@example.com"},
            {"id": 2, "email": "second@example.com"},
        ]
    )
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setenv("alfred_workflow_cache", str(tmp_path))
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.aliases("")

    assert [item["title"] for item in json.loads(output[0])["items"]] == [
        "first@example.com",
        "second@example.com",
    ]


def test_alias_search_matches_fuzzy_subsequences_and_caches_results(monkeypatch, tmp_path):
    client = FakeClient(aliases=[{"id": 9, "email": "foo.storage134@example.com"}])
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setenv("alfred_workflow_cache", str(tmp_path))
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.aliases("fost")
    assert [item["title"] for item in json.loads(output[-1])["items"]] == [
        "foo.storage134@example.com"
    ]

    alfred.aliases("stor")
    assert [item["title"] for item in json.loads(output[-1])["items"]] == [
        "foo.storage134@example.com"
    ]
    assert client.list_calls == 1


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


def test_create_can_emit_existing_status_for_workflow(monkeypatch):
    client = FakeClient(result={"reverse_alias_address": "old@aleeas.com", "existed": True})
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.create(123, "person@example.com", True)

    assert json.loads(output[0]) == {
        "address": "old@aleeas.com",
        "existed": True,
    }
    assert client.closed


def test_create_emits_a_concise_cli_error(monkeypatch, capsys):
    class ErrorClient(FakeClient):
        def create_contact(self, alias_id, recipient):
            raise alfred.SimpleLoginError("SimpleLogin API error 400: bad recipient")

    client = ErrorClient()
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)

    with pytest.raises(alfred.typer.Exit):
        alfred.create(123, "not-an-email")
    assert "Error: SimpleLogin API error 400: bad recipient" in capsys.readouterr().err
    assert client.closed


def test_new_aliases_emits_available_suffixes_and_default_mailbox(monkeypatch):
    class OptionsClient(FakeClient):
        def list_alias_options(self):
            return {
                "can_create": True,
                "prefix_suggestion": "hello",
                "suffixes": [
                    {
                        "suffix": ".example.com",
                        "signed_suffix": ".example.com.signature",
                        "is_premium": False,
                    }
                ],
            }

        def list_mailboxes(self):
            return [
                {"id": 9, "email": "mail@example.com", "verified": True, "default": True}
            ]

    client = OptionsClient()
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.new_aliases("")

    item = json.loads(output[0])["items"][0]
    assert item["title"] == "hello.example.com"
    assert item["subtitle"] == "Alias suffix · sends to mail@example.com"
    assert item["arg"] == ".example.com.signature"
    assert item["variables"] == {
        "mailbox_id": "9",
        "prefix_suggestion": "hello",
        "alias_suffix": ".example.com",
        "signed_suffix": ".example.com.signature",
    }
    assert client.closed


def test_create_custom_prints_created_alias(monkeypatch):
    class CreateClient(FakeClient):
        def create_custom_alias(self, prefix, signed_suffix, mailbox_ids):
            self.created_alias = (prefix, signed_suffix, mailbox_ids)
            return {"email": "hello@example.com"}

    client = CreateClient()
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.create_custom("hello", ".example.com.signature", 9)

    assert client.created_alias == ("hello", ".example.com.signature", [9])
    assert output == ["hello@example.com"]
    assert client.closed


def test_create_prints_only_reverse_alias_address(monkeypatch):
    client = FakeClient(result={"reverse_alias_address": "reverse@example.com"})
    output = []
    monkeypatch.setattr(alfred, "get_client", lambda api_key: client)
    monkeypatch.setattr(alfred.typer, "echo", output.append)

    alfred.create(123, "person@example.com")

    assert client.created == (123, "person@example.com")
    assert output == ["reverse@example.com"]
    assert client.closed
