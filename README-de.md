# openplz-mcp 🧭

mcp-name: io.github.mohammad-abbasi-sh/openplz-mcp

Inoffizieller **Nur-Lesen**-MCP-Server für **deutsche Postdaten** über die [OpenPLZ API](https://openplzapi.org) (vom openpotato-Projekt): Orte, Straßen, Gemeinden, Kreise, Regierungsbezirke und die 16 Bundesländer — mit den amtlichen Verwaltungsschlüsseln. Kein Schlüssel, keine Anmeldung nötig.

> Gebaut von Mohammad Abbasi im Rahmen der „Germany MCP factory". Keine Verbindung zur OpenPLZ API / zum openpotato-Projekt.

## Für KI-Agenten

In die MCP-Client-Konfiguration eintragen (stdio):

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

Oder lokal starten: `python -m openplz_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|--------------|
| `openplz_lookup_postal_code` | Zu welchem Ort (oder welchen Orten) eine deutsche Postleitzahl gehört |
| `openplz_search_locality` | Orte nach Namen suchen, optional innerhalb einer Postleitzahl |
| `openplz_search_street` | Straßen nach Name, Postleitzahl und/oder Ort suchen |
| `openplz_full_text_search` | Freitextsuche über Straßenname, Postleitzahl und Stadt |
| `openplz_list_federal_states` | Alle 16 Bundesländer mit Schlüssel + Hauptstadt |
| `openplz_admin_children` | Einen Schritt im Verwaltungsbaum nach unten gehen (Land → Kreis → Gemeinde …) |
| `openplz_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

Beispielausgabe (`openplz_lookup_postal_code` / 10115):

```json
{"postal_code": "10115", "count": 1,
 "localities": [{"postal_code": "10115", "name": "Berlin",
   "municipality": {"key": "11000000", "name": "Berlin, Stadt", "type": "Kreisfreie Stadt"},
   "federal_state": {"key": "11", "name": "Berlin"}}]}
```

Hinweise:
- Eine deutsche Postleitzahl hat genau 5 Ziffern (z. B. 10115 = Berlin-Mitte, 80331 = München).
- Amtliche Verwaltungsschlüssel: Bundesländer `"01"`–`"16"` (Berlin `"11"`, Bayern `"09"`), Kreise 5-stellig (`"11000"` = Berlin), Gemeinden 8-stellig (`"09162000"` = München). Mit `openplz_admin_children` nutzen — z. B. `federal_state "11" → districts` liefert den einzigen Berliner Kreis; `district "11000" → localities` listet Berlins Orte.
- Die Straßennamensuche trifft die gespeicherte, abgekürzte Form (z. B. `"Ackerstr."`). Für freie Anfragen (z. B. `"10115 Berlin"` oder `"München Marienplatz"`) `openplz_full_text_search` verwenden.
- Eine Postleitzahl kann mehrere Orte umfassen, und ein Ort kann mehrere Postleitzahlen haben — `openplz_lookup_postal_code` gibt alle zurück.
- Die Daten decken nur Deutschland ab (`/de/`-Endpunkte); die OpenPLZ API bedient außerdem Österreich (`/at/`) und die Schweiz (`/ch/`), die dieser Server nicht anbietet.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
