# openplz-mcp 🧭

mcp-name: io.github.mohammad-abbasi-sh/openplz-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **داده‌های پستی آلمان** از طریق [OpenPLZ API](https://openplzapi.org) (پروژهٔ openpotato): شهرها و روستاها، خیابان‌ها، شهرداری‌ها، بخش‌ها، ناحیه‌های دولتی و ۱۶ ایالت فدرال (Bundesländer) — همراه با کدهای رسمی اداری. بدون کلید و بدون ورود.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP آلمان». وابسته به OpenPLZ API / پروژهٔ openpotato نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP Client اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m openplz_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `openplz_lookup_postal_code` | کد پستی آلمان متعلق به کدام شهر (یا شهرها) است |
| `openplz_search_locality` | جست‌وجوی شهرها بر اساس نام، اختیاری درون یک کد پستی |
| `openplz_search_street` | جست‌وجوی خیابان‌ها بر اساس نام، کد پستی و/یا شهر |
| `openplz_full_text_search` | جست‌وجوی آزاد در نام خیابان، کد پستی و شهر |
| `openplz_list_federal_states` | هر ۱۶ ایالت فدرال با کد + مرکز |
| `openplz_admin_children` | یک قدم پایین‌تر در درخت اداری (ایالت ← بخش ← شهرداری …) |
| `openplz_health` | بررسی دسترسی به API (ok / blocked / error) — یک درخواست مؤدبانه |

نمونهٔ خروجی (`openplz_lookup_postal_code` / 10115):

```json
{"postal_code": "10115", "count": 1,
 "localities": [{"postal_code": "10115", "name": "Berlin",
   "municipality": {"key": "11000000", "name": "Berlin, Stadt", "type": "Kreisfreie Stadt"},
   "federal_state": {"key": "11", "name": "Berlin"}}]}
```

نکته‌ها:
- کد پستی آلمان دقیقاً ۵ رقم است (مثلاً 10115 = برلین-میته، 80331 = مونیخ).
- کدهای رسمی اداری: ایالت‌ها `"01"` تا `"16"` (برلین `"11"`، بایرن `"09"`)، بخش‌ها ۵ رقمی (`"11000"` = برلین)، شهرداری‌ها ۸ رقمی (`"09162000"` = مونیخ). با `openplz_admin_children` استفاده کنید — مثلاً `federal_state "11" → districts` تنها بخش برلین را برمی‌گرداند؛ `district "11000" → localities` شهرهای برلین را فهرست می‌کند.
- جست‌وجوی نام خیابان با شکل ذخیره‌شدهٔ مخفف مطابقت می‌کند (مثلاً `"Ackerstr."`). برای جست‌وجوی آزاد (مثلاً `"10115 Berlin"` یا `"München Marienplatz"`) از `openplz_full_text_search` استفاده کنید.
- یک کد پستی می‌تواند چند شهر را پوشش دهد و یک شهر می‌تواند چند کد پستی داشته باشد — `openplz_lookup_postal_code` همه را برمی‌گرداند.
- داده‌ها فقط آلمان را پوشش می‌دهند (مسیرهای `/de/`)؛ OpenPLZ API اتریش (`/at/`) و سوئیس (`/ch/`) را هم دارد که این سرور ارائه نمی‌کند.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
