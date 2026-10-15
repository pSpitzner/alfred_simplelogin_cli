from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class SimpleLoginError(RuntimeError):
    """An API or client-side SimpleLogin error."""


@dataclass
class SimpleLoginClient:
    api_key: str
    base_url: str = "https://api.simplelogin.io"
    timeout: float = 20.0

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authentication": self.api_key,
                "Accept": "application/json",
            },
            timeout=self.timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SimpleLoginClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise SimpleLoginError(f"HTTP request failed: {exc}") from exc

        if response.is_success:
            if not response.content:
                return {}
            try:
                return response.json()
            except ValueError as exc:
                raise SimpleLoginError(
                    f"SimpleLogin returned non-JSON data (HTTP {response.status_code})."
                ) from exc

        # Avoid dumping the API key or arbitrary response headers.
        try:
            body = response.json()
            detail = body.get("error") or body.get("message") or str(body)
        except ValueError:
            detail = response.text[:500].strip()

        if not detail:
            detail = response.reason_phrase

        raise SimpleLoginError(
            f"SimpleLogin API error {response.status_code}: {detail}"
        )

    def verify_api_key(self) -> None:
        """Verify credentials with a single lightweight aliases request."""
        self._request(
            "GET",
            "/api/v2/aliases",
            params={"page_id": 0},
        )

    def list_aliases(self) -> list[dict[str, Any]]:
        """Fetch every alias, following the documented 20-item pagination."""
        aliases: list[dict[str, Any]] = []
        page_id = 0

        while True:
            data = self._request(
                "GET",
                "/api/v2/aliases",
                params={"page_id": page_id},
            )
            page = data.get("aliases") or []
            if not page:
                break

            aliases.extend(page)

            # The API documents max 20 aliases/page. A short page is the end.
            if len(page) < 20:
                break
            page_id += 1

        return aliases

    def list_alias_options(self) -> dict[str, Any]:
        """Fetch available custom-alias suffixes and prefix suggestions."""
        return self._request("GET", "/api/v5/alias/options")

    def list_mailboxes(self) -> list[dict[str, Any]]:
        """Fetch the user's mailbox destinations."""
        data = self._request("GET", "/api/v2/mailboxes")
        return data.get("mailboxes") or []

    def create_custom_alias(
        self,
        prefix: str,
        signed_suffix: str,
        mailbox_ids: list[int],
    ) -> dict[str, Any]:
        """Create a custom alias using an opaque signed suffix from the API."""
        return self._request(
            "POST",
            "/api/v3/alias/custom/new",
            json={
                "alias_prefix": prefix,
                "signed_suffix": signed_suffix,
                "mailbox_ids": mailbox_ids,
            },
        )

    def list_contacts(self, alias_id: int) -> list[dict[str, Any]]:
        """Fetch every contact for an alias."""
        contacts: list[dict[str, Any]] = []
        page_id = 0

        while True:
            data = self._request(
                "GET",
                f"/api/aliases/{alias_id}/contacts",
                params={"page_id": page_id},
            )
            page = data.get("contacts") or []
            if not page:
                break

            contacts.extend(page)

            if len(page) < 20:
                break
            page_id += 1

        return contacts

    def create_contact(
        self, alias_id: int, contact: str
    ) -> dict[str, Any]:
        """Return an existing reverse alias or create one for this contact."""
        normalized_contact = contact.strip().casefold()
        for existing in self.list_contacts(alias_id):
            existing_contact = str(existing.get("contact") or "").strip().casefold()
            if normalized_contact and existing_contact == normalized_contact:
                return {**existing, "existed": True}

        return self._request(
            "POST",
            f"/api/aliases/{alias_id}/contacts",
            json={"contact": contact},
        )

    def find_alias(
        self, aliases: list[dict[str, Any]], selector: str
    ) -> dict[str, Any]:
        """Resolve an alias by numeric ID, exact email/name, or unique substring."""
        selector_lower = selector.casefold()

        # Numeric ID.
        if selector.isdigit():
            alias_id = int(selector)
            matches = [a for a in aliases if int(a.get("id", -1)) == alias_id]
            if len(matches) == 1:
                return matches[0]

        # Exact email or exact name.
        exact = [
            a for a in aliases
            if str(a.get("email", "")).casefold() == selector_lower
            or str(a.get("name") or "").casefold() == selector_lower
        ]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise SimpleLoginError(
                f"'{selector}' matches multiple aliases exactly."
            )

        # Unique substring match.
        partial = [
            a for a in aliases
            if selector_lower in str(a.get("email", "")).casefold()
            or selector_lower in str(a.get("name") or "").casefold()
        ]
        if len(partial) == 1:
            return partial[0]
        if not partial:
            raise SimpleLoginError(f"No alias found for '{selector}'.")
        raise SimpleLoginError(
            f"'{selector}' matches {len(partial)} aliases; use the alias ID "
            "or exact email."
        )
