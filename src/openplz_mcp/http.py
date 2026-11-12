"""HTTP layer for openplz_mcp — plain httpx GETs against the OpenPLZ API.

No key, no login. One retry on 429/5xx; error taxonomy (403/429/other).
The OpenPLZ API is a free community service (openplzapi.org, by the
openpotato project) serving German postal data: localities, streets,
municipalities, districts, government regions and the 16 federal states.
"""
from __future__ import annotations

import os
import ssl
import time

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 25.0
PROBE_URL = "https://openplzapi.org/de/FederalStates"
SOURCE = "OpenPLZ API (openplzapi.org)"


class OpenPlzMcpError(RuntimeError):
    pass


def _verify():
    """TLS trust store: the OS bundle when present, else httpx/certifi."""
    for path in (
        "/etc/ssl/certs/ca-certificates.crt",
        ssl.get_default_verify_paths().openssl_cafile,
    ):
        if path and os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return True


def _client() -> httpx.Client:
    # NOTE: we read the proxy URL from the environment but never log it.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    return httpx.Client(
        headers={"User-Agent": UA, "Accept": "application/json, */*"},
        timeout=TIMEOUT,
        proxy=proxy or None,
        trust_env=False,
        verify=_verify(),
        follow_redirects=True,
    )


def fetch_text(url: str) -> str:
    """GET one URL and return its text. One retry on 429/5xx."""
    last_exc: Exception | None = None
    r: httpx.Response | None = None
    for attempt in range(2):
        try:
            with _client() as c:
                r = c.get(url)
        except httpx.HTTPError as e:
            last_exc = e
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise OpenPlzMcpError(f"network error fetching {url}: {e}") from e
        if r.status_code in (429, 500, 502, 503):
            if attempt == 0:
                time.sleep(1.0)
                continue
        break
    assert r is not None  # loop always assigns r or raises
    if r.status_code == 403:
        raise OpenPlzMcpError(
            f"{SOURCE} returned HTTP 403 for {url} (bot wall) — try again later"
        )
    if r.status_code == 400:
        raise OpenPlzMcpError(
            f"{SOURCE} rejected the request (HTTP 400) — check the "
            "postal code, state key or search term"
        )
    if r.status_code == 404:
        raise OpenPlzMcpError(
            f"{SOURCE} returned HTTP 404 for {url} — unknown key or path"
        )
    if r.status_code == 429:
        raise OpenPlzMcpError(
            f"{SOURCE} rate-limited the request (HTTP 429) — try again later"
        )
    if r.status_code != 200:
        raise OpenPlzMcpError(f"{SOURCE} returned HTTP {r.status_code} for {url}")
    return r.text


def health_check() -> dict:
    """One polite probe of the source API.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `openplz_health` tool
    and the daily smoke CI.
    """
    url = PROBE_URL
    try:
        fetch_text(url)
    except OpenPlzMcpError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
