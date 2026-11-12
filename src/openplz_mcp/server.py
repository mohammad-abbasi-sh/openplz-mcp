"""MCP server: unofficial read-only access to German postal data via the
OpenPLZ API (openplzapi.org) — localities, streets, municipalities,
districts, government regions and the 16 federal states. No key, no login.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for German postal data — the OpenPLZ API
(openplzapi.org, by the openpotato project): localities, streets,
municipalities, districts, government regions and the 16 federal states
(Bundesländer), with the official administrative keys (federal states
"01".."16", e.g. Berlin "11", Bayern "09"; districts 5 digits, e.g.
"11000" Berlin; municipalities 8 digits, e.g. "09162000" München).
A German postal code is exactly 5 digits (e.g. 10115 = Berlin-Mitte).
Street-name search matches the stored, abbreviated form (e.g.
"Ackerstr."); for free-form queries use openplz_full_text_search.
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — \
Germany MCP factory.
"""

_SOURCE = "OpenPLZ API v1 (openplzapi.org)"
_DISCLAIMER = "Unofficial read-only data from the OpenPLZ API; verify on openplzapi.org before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("openplz-mcp", instructions=INSTRUCTIONS)


@mcp.tool()
def openplz_lookup_postal_code(postal_code: str) -> str:
    """Which locality (or localities) a German postal code belongs to.
    postal_code: exactly 5 digits, e.g. 10115 (Berlin-Mitte)."""
    try:
        rows = _dom.parse_localities(
            _http.fetch_text(_dom.localities_url(postal_code=postal_code, limit=50)))
    except (_http.OpenPlzMcpError, ValueError) as e:
        return _err(e)
    return _ok({"postal_code": postal_code.strip(), "count": len(rows),
                "localities": rows})


@mcp.tool()
def openplz_search_locality(name: str, postal_code: str | None = None,
                            limit: int = 20) -> str:
    """Search German localities (Orte) by name, optionally restricted to
    one postal code. name: e.g. München (matches München, Münchenbernsdorf
    ...). Returns each locality's postal code, municipality, district and
    federal state. limit: 1..50 (default 20)."""
    try:
        rows = _dom.parse_localities(_http.fetch_text(
            _dom.localities_url(postal_code=postal_code, name=name,
                                limit=limit)))
    except (_http.OpenPlzMcpError, ValueError) as e:
        return _err(e)
    return _ok({"name": (name or "").strip(),
                "postal_code": postal_code,
                "total_results": len(rows), "limit": limit,
                "count": len(rows), "localities": rows})


@mcp.tool()
def openplz_search_street(name: str | None = None,
                          postal_code: str | None = None,
                          locality: str | None = None,
                          limit: int = 20) -> str:
    """Search German streets by name, postal code and/or locality — at
    least one filter is required. name matches the stored, abbreviated
    form (e.g. "Ackerstr."); for free-form queries use
    openplz_full_text_search. Returns street, postal code, locality,
    borough/suburb, municipality and federal state. limit: 1..50."""
    try:
        rows = _dom.parse_streets(_http.fetch_text(
            _dom.streets_url(name=name, postal_code=postal_code,
                             locality=locality, limit=limit)))
    except (_http.OpenPlzMcpError, ValueError) as e:
        return _err(e)
    return _ok({"name": name, "postal_code": postal_code,
                "locality": locality, "total_results": len(rows),
                "limit": limit, "count": len(rows), "streets": rows})


@mcp.tool()
def openplz_full_text_search(search_term: str, limit: int = 20) -> str:
    """Free-form street search across street name, postal code and city,
    e.g. "10115 Berlin" or "München Marienplatz". Returns matching
    streets with postal code, locality, borough/suburb, municipality and
    federal state. limit: 1..50 (default 20)."""
    try:
        rows = _dom.parse_streets(_http.fetch_text(
            _dom.full_text_url(search_term, limit=limit)))
    except (_http.OpenPlzMcpError, ValueError) as e:
        return _err(e)
    return _ok({"search_term": (search_term or "").strip(),
                "total_results": len(rows), "limit": limit,
                "count": len(rows), "streets": rows})


@mcp.tool()
def openplz_list_federal_states() -> str:
    """All 16 German federal states (Bundesländer) with their official
    key ("01".."16") and seat of government (capital)."""
    try:
        rows = _dom.parse_federal_states(
            _http.fetch_text(_dom.federal_states_url()))
    except (_http.OpenPlzMcpError, ValueError) as e:
        return _err(e)
    return _ok({"count": len(rows), "federal_states": rows})


@mcp.tool()
def openplz_admin_children(parent_type: str, parent_key: str,
                          child_type: str, limit: int = 20) -> str:
    """Walk one step down the German administrative tree.
    parent_type: federal_state | government_region | district.
    parent_key: official key, e.g. "11" (Berlin), "09" (Bayern),
    "11000" (Berlin district), "091" (Oberbayern region).
    child_type: districts | government_regions | localities |
    municipalities | municipal_associations — only the combinations the
    API offers (e.g. federal_state -> districts, district -> localities).
    limit: 1..50 (default 20)."""
    try:
        rows = _dom.parse_admin_children(_http.fetch_text(
            _dom.admin_children_url(parent_type, parent_key, child_type,
                                    limit=limit)))
    except (_http.OpenPlzMcpError, ValueError) as e:
        return _err(e)
    return _ok({"parent_type": parent_type, "parent_key": parent_key,
                "child_type": child_type, "total_results": len(rows),
                "limit": limit, "count": len(rows), "children": rows})


@mcp.tool()
def openplz_health() -> str:
    """Check whether the OpenPLZ API is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
