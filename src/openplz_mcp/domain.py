"""Domain logic: shape OpenPLZ API responses into compact dicts (stdlib only).

Data source: the free OpenPLZ API v1 (openplzapi.org, by the openpotato
project) — German postal data, no key, no login. German endpoints live
under /de/ (the API also serves /at/ Austria and /ch/ Switzerland, which
this server does not expose). All responses are plain JSON arrays.

- /de/Localities?postalCode=&name= — localities (Orte) with their
  municipality, district and federal state. A postal code can cover
  several localities; a locality can have several postal codes.
- /de/Streets?name=&postalCode=&locality= — streets (Straßen) with
  borough/suburb and the same administrative parents. NOTE (verified
  2026-11-12): `name` matches the stored, abbreviated form
  (e.g. "Ackerstr.") — it does NOT match "Friedrichstraße" via the
  prefix "Friedrichstr."/"Friedrichstr"; use full-text search for
  free-form street queries.
- /de/FullTextSearch?searchTerm= — streets matching a free-form term
  (street name, postal code, city).
- /de/FederalStates — the 16 Bundesländer with their seat of government.
- /de/FederalStates/{key}/Districts|GovernmentRegions|Localities|
  Municipalities|MunicipalAssociations,
  /de/GovernmentRegions/{key}/Districts|Localities|Municipalities|
  MunicipalAssociations,
  /de/Districts/{key}/Localities|Municipalities|MunicipalAssociations —
  the administrative tree below a state / region / district.
  Keys are the official AGS-style codes: federal states "01".."16"
  (Berlin "11", Bayern "09"), districts 5 digits ("11000" Berlin),
  municipalities 8 digits ("09162000" München).

The API returns camelCase keys; parsers normalise to snake_case and
keep the fields the API returns (no invented data).
"""
from __future__ import annotations

import json
import re
from urllib.parse import quote_plus

BASE = "https://openplzapi.org"

PLZ_RE = re.compile(r"^\d{5}$")
MAX_LIMIT = 50

# (parent_type, child_type) -> path segment template (German /de/ tree).
ADMIN_CHILDREN = {
    ("federal_state", "districts"): "FederalStates/{key}/Districts",
    ("federal_state", "government_regions"): "FederalStates/{key}/GovernmentRegions",
    ("federal_state", "localities"): "FederalStates/{key}/Localities",
    ("federal_state", "municipalities"): "FederalStates/{key}/Municipalities",
    ("federal_state", "municipal_associations"): "FederalStates/{key}/MunicipalAssociations",
    ("government_region", "districts"): "GovernmentRegions/{key}/Districts",
    ("government_region", "localities"): "GovernmentRegions/{key}/Localities",
    ("government_region", "municipalities"): "GovernmentRegions/{key}/Municipalities",
    ("government_region", "municipal_associations"): "GovernmentRegions/{key}/MunicipalAssociations",
    ("district", "localities"): "Districts/{key}/Localities",
    ("district", "municipalities"): "Districts/{key}/Municipalities",
    ("district", "municipal_associations"): "Districts/{key}/MunicipalAssociations",
}

PARENT_TYPES = sorted({p for p, _ in ADMIN_CHILDREN})
CHILD_TYPES = sorted({c for _, c in ADMIN_CHILDREN})


def validate_postal_code(code: str) -> str:
    """A German postal code is exactly 5 digits."""
    code = (code or "").strip()
    if not PLZ_RE.fullmatch(code):
        raise ValueError(
            f"bad postal code {code!r} (expected 5 digits, e.g. 10115)"
        )
    return code


def validate_limit(limit: int, default: int = 20) -> int:
    """Clamp a result limit to 1..50."""
    try:
        n = int(limit)
    except (TypeError, ValueError):
        raise ValueError(f"limit must be a number, got {limit!r}") from None
    if not 1 <= n <= MAX_LIMIT:
        raise ValueError(f"limit out of range: {limit} (expected 1..{MAX_LIMIT})")
    return n


def localities_url(postal_code: str | None = None, name: str | None = None,
                   limit: int = 20) -> str:
    q = [f"pageSize={validate_limit(limit)}"]
    if postal_code is not None:
        q.append(f"postalCode={validate_postal_code(postal_code)}")
    if name:
        q.append(f"name={quote_plus(name.strip())}")
    return f"{BASE}/de/Localities?{'&'.join(q)}"


def streets_url(name: str | None = None, postal_code: str | None = None,
                locality: str | None = None, limit: int = 20) -> str:
    if not (name or postal_code or locality):
        raise ValueError(
            "street search needs at least one of name, postal_code, locality"
        )
    q = [f"pageSize={validate_limit(limit)}"]
    if name:
        q.append(f"name={quote_plus(name.strip())}")
    if postal_code is not None:
        q.append(f"postalCode={validate_postal_code(postal_code)}")
    if locality:
        q.append(f"locality={quote_plus(locality.strip())}")
    return f"{BASE}/de/Streets?{'&'.join(q)}"


def full_text_url(search_term: str, limit: int = 20) -> str:
    term = (search_term or "").strip()
    if not term:
        raise ValueError("search_term must not be empty")
    return (f"{BASE}/de/FullTextSearch?searchTerm={quote_plus(term)}"
            f"&pageSize={validate_limit(limit)}")


def federal_states_url() -> str:
    return f"{BASE}/de/FederalStates"


def admin_children_url(parent_type: str, parent_key: str,
                       child_type: str, limit: int = 20) -> str:
    """URL for one step down the administrative tree.

    parent_type: federal_state | government_region | district.
    child_type: districts | government_regions | localities |
    municipalities | municipal_associations (only the combinations the
    API offers; anything else raises with the valid list)."""
    parent = (parent_type or "").strip().lower().replace("-", "_")
    child = (child_type or "").strip().lower().replace("-", "_")
    key = (parent_key or "").strip()
    if not key:
        raise ValueError("parent_key must not be empty")
    template = ADMIN_CHILDREN.get((parent, child))
    if template is None:
        valid = sorted(
            f"{p} -> {c}" for (p, c) in ADMIN_CHILDREN
        )
        raise ValueError(
            f"no {child!r} under {parent!r}; valid combinations: "
            + "; ".join(valid)
        )
    return (f"{BASE}/de/{template.format(key=quote_plus(key))}"
            f"?pageSize={validate_limit(limit)}")


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _norm(value):
    """Recursively camelCase -> snake_case for dict keys."""
    if isinstance(value, dict):
        return {_snake(k): _norm(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_norm(v) for v in value]
    return value


def _parse_list(text: str, what: str) -> list:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid {what} response: {e}") from e
    if not isinstance(payload, list):
        raise ValueError(f"unexpected {what} shape: not a JSON array")
    return [_norm(row) if isinstance(row, dict) else row for row in payload]


def parse_localities(text: str) -> list:
    """Locality rows -> [{postal_code, name, municipality, district?,
    federal_state}]."""
    rows = _parse_list(text, "localities")
    out = []
    for r in rows:
        out.append({
            "postal_code": r.get("postal_code") or "",
            "name": r.get("name") or "",
            "municipality": r.get("municipality") or {},
            "district": r.get("district") or None,
            "federal_state": r.get("federal_state") or {},
        })
    return out


def parse_streets(text: str) -> list:
    """Street rows -> [{name, postal_code, locality, borough, suburb,
    municipality, federal_state}]."""
    rows = _parse_list(text, "streets")
    out = []
    for r in rows:
        out.append({
            "name": r.get("name") or "",
            "postal_code": r.get("postal_code") or "",
            "locality": r.get("locality") or "",
            "borough": r.get("borough") or None,
            "suburb": r.get("suburb") or None,
            "municipality": r.get("municipality") or {},
            "federal_state": r.get("federal_state") or {},
        })
    return out


def parse_federal_states(text: str) -> list:
    """Federal-state rows -> [{key, name, seat_of_government}]."""
    rows = _parse_list(text, "federal states")
    out = []
    for r in rows:
        out.append({
            "key": r.get("key") or "",
            "name": r.get("name") or "",
            "seat_of_government": r.get("seat_of_government") or "",
        })
    out.sort(key=lambda s: s["key"])
    return out


def parse_admin_children(text: str) -> list:
    """Administrative child rows (districts / municipalities / government
    regions / localities / municipal associations) — normalised, fields
    kept as the API returns them."""
    return _parse_list(text, "administrative children")
