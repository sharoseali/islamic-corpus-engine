"""Quran Foundation (quran.com) API client.

OAuth2 client_credentials flow with token caching, polite throttling, and
retry with backoff on transient failures.
"""

import time

import httpx

from app.core.config import Settings

CONTENT_PREFIX = "/content/api/v4"

# Be a respectful API citizen: max ~3 requests/second.
MIN_REQUEST_INTERVAL = 0.35
RETRY_ATTEMPTS = 4
RETRY_BACKOFF = 2.0  # seconds, doubled per attempt


class QuranFoundationClient:
    def __init__(self, settings: Settings):
        if not settings.QF_CLIENT_ID or not settings.QF_CLIENT_SECRET:
            raise RuntimeError(
                "QF_CLIENT_ID / QF_CLIENT_SECRET are not set - add them to .env"
            )
        self._settings = settings
        self._http = httpx.Client(timeout=30.0)
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._last_request_at: float = 0.0

    # ------------------------------------------------------------------ #

    def get(self, path: str, params: dict | None = None) -> httpx.Response:
        """GET a content API path (e.g. "/chapters"), authenticated."""
        url = f"{self._settings.QF_API_BASE}{CONTENT_PREFIX}{path}"
        last_error: Exception | None = None
        for attempt in range(RETRY_ATTEMPTS):
            self._throttle()
            try:
                response = self._http.get(
                    url,
                    params=params,
                    headers={
                        "x-auth-token": self._access_token(),
                        "x-client-id": self._settings.QF_CLIENT_ID,
                    },
                )
                if response.status_code < 500 and response.status_code != 429:
                    response.raise_for_status()
                    return response
                last_error = httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            except httpx.TransportError as exc:
                last_error = exc
            time.sleep(RETRY_BACKOFF * (2**attempt))
        raise RuntimeError(f"GET {url} failed after {RETRY_ATTEMPTS} attempts") from last_error

    # ------------------------------------------------------------------ #

    def _access_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token
        response = self._http.post(
            f"{self._settings.QF_OAUTH_BASE}/oauth2/token",
            auth=(self._settings.QF_CLIENT_ID, self._settings.QF_CLIENT_SECRET),
            data={"grant_type": "client_credentials", "scope": "content"},
        )
        response.raise_for_status()
        payload = response.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 3600)
        return self._token

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_at
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_at = time.time()
