from simplelogin_cli.client import SimpleLoginClient


def test_find_alias_by_exact_email():
    client = SimpleLoginClient("test")
    aliases = [
        {"id": 10, "email": "foo@aleeas.com", "name": "Foo"},
        {"id": 11, "email": "bar@aleeas.com", "name": "Bar"},
    ]

    assert client.find_alias(aliases, "foo@aleeas.com")["id"] == 10
    client.close()


def test_find_alias_by_id():
    client = SimpleLoginClient("test")
    aliases = [{"id": 10, "email": "foo@aleeas.com", "name": "Foo"}]

    assert client.find_alias(aliases, "10")["email"] == "foo@aleeas.com"
    client.close()


def test_create_contact_reuses_existing_contact_without_posting(monkeypatch):
    client = SimpleLoginClient("test")
    posts = []
    monkeypatch.setattr(
        client,
        "list_contacts",
        lambda alias_id: [
            {
                "id": 77,
                "contact": "Person@Example.com",
                "reverse_alias_address": "existing@aleeas.com",
            }
        ],
    )
    monkeypatch.setattr(
        client,
        "_request",
        lambda *args, **kwargs: posts.append((args, kwargs)),
    )

    result = client.create_contact(41, " person@example.com ")

    assert result == {
        "id": 77,
        "contact": "Person@Example.com",
        "reverse_alias_address": "existing@aleeas.com",
        "existed": True,
    }
    assert posts == []
    client.close()


def test_create_contact_posts_when_contact_is_new(monkeypatch):
    client = SimpleLoginClient("test")
    calls = []
    monkeypatch.setattr(client, "list_contacts", lambda alias_id: [])
    monkeypatch.setattr(
        client,
        "_request",
        lambda method, path, **kwargs: calls.append((method, path, kwargs))
        or {"reverse_alias_address": "new@aleeas.com"},
    )

    result = client.create_contact(41, "new@example.com")

    assert result == {"reverse_alias_address": "new@aleeas.com"}
    assert calls == [
        (
            "POST",
            "/api/aliases/41/contacts",
            {"json": {"contact": "new@example.com"}},
        )
    ]
    client.close()


def test_custom_alias_api_methods_use_documented_endpoints(monkeypatch):
    client = SimpleLoginClient("test")
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        if path == "/api/v5/alias/options":
            return {"suffixes": []}
        if path == "/api/v2/mailboxes":
            return {"mailboxes": [{"id": 9}]}
        return {"email": "hello@example.com"}

    monkeypatch.setattr(client, "_request", fake_request)

    assert client.list_alias_options() == {"suffixes": []}
    assert client.list_mailboxes() == [{"id": 9}]
    assert client.create_custom_alias("hello", ".example.com.sig", [9]) == {
        "email": "hello@example.com"
    }
    assert calls == [
        ("GET", "/api/v5/alias/options", {}),
        ("GET", "/api/v2/mailboxes", {}),
        (
            "POST",
            "/api/v3/alias/custom/new",
            {
                "json": {
                    "alias_prefix": "hello",
                    "signed_suffix": ".example.com.sig",
                    "mailbox_ids": [9],
                }
            },
        ),
    ]
    client.close()
