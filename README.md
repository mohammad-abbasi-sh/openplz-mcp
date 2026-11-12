# openplz-mcp 🧭

mcp-name: io.github.mohammad-abbasi-sh/openplz-mcp

Unofficial **read-only** MCP server for **German postal data** via the [OpenPLZ API](https://openplzapi.org) (by the openpotato project): localities, streets, municipalities, districts, government regions and the 16 federal states (Bundesländer) — with the official administrative keys. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with the OpenPLZ API / openpotato project.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "openplz": {
      "command": "uvx",
      "args": ["openplz-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m openplz_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `openplz_lookup_postal_code` | Which locality (or localities) a German postal code belongs to |
| `openplz_search_locality` | Search localities (Orte) by name, optionally within one postal code |
| `openplz_search_street` | Search streets by name, postal code and/or locality |
| `openplz_full_text_search` | Free-form street search across street name, postal code and city |
| `openplz_list_federal_states` | All 16 federal states (Bundesländer) with key + capital |
| `openplz_admin_children` | Walk one step down the administrative tree (state → district → municipality …) |
| `openplz_health` | Reachability check (ok / blocked / error) — one polite request |

Example output (`openplz_lookup_postal_code` / 10115):

```json
{"postal_code": "10115", "count": 1,
 "localities": [{"postal_code": "10115", "name": "Berlin",
   "municipality": {"key": "11000000", "name": "Berlin, Stadt", "type": "Kreisfreie Stadt"},
   "federal_state": {"key": "11", "name": "Berlin"}}]}
```

Notes:
- A German postal code is exactly 5 digits (e.g. 10115 = Berlin-Mitte, 80331 = München).
- Official administrative keys: federal states `"01"`–`"16"` (Berlin `"11"`, Bayern `"09"`), districts 5 digits (`"11000"` = Berlin), municipalities 8 digits (`"09162000"` = München). Use them with `openplz_admin_children` — e.g. `federal_state "11" → districts` returns the single Berlin district; `district "11000" → localities` lists Berlin's localities.
- Street-name search matches the stored, abbreviated form (e.g. `"Ackerstr."`). For free-form queries (e.g. `"10115 Berlin"` or `"München Marienplatz"`) use `openplz_full_text_search`.
- A postal code can cover several localities, and a locality can have several postal codes — `openplz_lookup_postal_code` returns all of them.
- Data covers Germany only (`/de/` endpoints); the OpenPLZ API also serves Austria (`/at/`) and Switzerland (`/ch/`), which this server does not expose.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
