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
