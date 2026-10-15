import pytest

from simplelogin_cli import main
from simplelogin_cli.client import SimpleLoginError


def test_get_api_key_falls_back_to_keyring(monkeypatch):
    monkeypatch.delenv("SIMPLELOGIN_API_KEY", raising=False)
    monkeypatch.setattr(
        main.keyring, "get_password", lambda service, account: " saved-token "
    )

    assert main.get_api_key(None) == "saved-token"


def test_get_api_key_prefers_environment(monkeypatch):
    monkeypatch.setenv("SIMPLELOGIN_API_KEY", "environment-token")

    def unexpected_keyring_lookup(service, account):
        raise AssertionError("unexpected keyring lookup")

    monkeypatch.setattr(main.keyring, "get_password", unexpected_keyring_lookup)

    assert main.get_api_key(None) == "environment-token"


def test_login_verifies_token_before_saving(monkeypatch):
    saved = {}
    events = []

    class Client:
        def verify_api_key(self):
            events.append("verify")

        def close(self):
            events.append("close")

    monkeypatch.setattr(main.typer, "prompt", lambda *args, **kwargs: "my-token")
    monkeypatch.setattr(main, "get_client", lambda token: Client())
    def save_password(service, account, token):
        events.append("save")
        saved.update(service=service, account=account, token=token)

    monkeypatch.setattr(main.keyring, "set_password", save_password)
    monkeypatch.setattr(main.typer, "echo", lambda message: None)

    main.login()

    assert events == ["verify", "close", "save"]
    assert saved == {
        "service": main.KEYRING_SERVICE,
        "account": main.KEYRING_ACCOUNT,
        "token": "my-token",
    }


def test_login_does_not_save_invalid_token(monkeypatch):
    saved = []

    class Client:
        def verify_api_key(self):
            raise SimpleLoginError("SimpleLogin API error 401: Unauthorized")

        def close(self):
            pass

    monkeypatch.setattr(main.typer, "prompt", lambda *args, **kwargs: "bad-token")
    monkeypatch.setattr(main, "get_client", lambda token: Client())
    monkeypatch.setattr(
        main.keyring,
        "set_password",
        lambda *args: saved.append(args),
    )

    with pytest.raises(main.typer.BadParameter, match="Could not verify API token"):
        main.login()

    assert saved == []
