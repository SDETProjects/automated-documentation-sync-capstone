# Data Files

JSON data files consumed by the **Spend Forecast API** (`ForecastDataService`, `spend_api_router.py`).

## Files

| File | Purpose | Schema |
|------|---------|--------|
| `spend_records.json` | Daily spend records | Array of `{ "date": "YYYY-MM-DD", "amount": number }` |
| `budgets.json` | Budget configuration | `{ "overall": number, "categories": [{ "id": string, "label": string, "budget": number }] }` |

## `spend_records.json`

```json
[
  { "date": "2026-08-01", "amount": 1200.00 },
  { "date": "2026-08-02", "amount": 980.50 },
  { "date": "2026-08-03", "amount": 1450.75 }
]
```

- **Date format**: ISO 8601 (`YYYY-MM-DD`)
- **Amount**: Numeric (float), currency-agnostic
- **Ordering**: Any order; service sorts by date ascending
- **Filtering**: `ForecastDataService.get_actual_spend(period)` returns records where `date.startswith(period)` (e.g., `"2026-08"`)

### Adding Records

Append to the array. No deduplication — if duplicate dates exist, both amounts are summed in projections.

## `budgets.json`

```json
{
  "overall": 35000.00,
  "categories": [
    { "id": "engineering", "label": "Engineering", "budget": 15000.00 },
    { "id": "marketing", "label": "Marketing", "budget": 8000.00 },
    { "id": "operations", "label": "Operations", "budget": 12000.00 }
  ]
}
```

- **overall**: Optional global budget threshold (number or `null`)
- **categories**: Optional array of category budgets
  - `id`: Machine-readable key (used in `category` query param)
  - `label`: Human-readable display name
  - `budget`: Threshold for that category

### Budget Lookup

- `GET /api/spend/forecast?period=2026-08` → uses `overall` budget
- `GET /api/spend/forecast?period=2026-08&category=engineering` → uses `categories[?id==engineering].budget`
- If no budget configured for the scope → `risk_flag: null` (FR-4 graceful degradation)

## Location

Default: `data/` at repo root.

Override in code:
```python
from documentation_sync.forecast_data_service import ForecastDataService
svc = ForecastDataService(data_dir=Path("/custom/path"))
```

Override in API server:
```python
from documentation_sync.spend_api_router import create_app
app = create_app(data_dir="/custom/path")
```

## Test Data

Tests use `tmp_path` fixtures with minimal JSON:

```python
# tests/conftest.py style
spend_file = tmp_path / "spend_records.json"
spend_file.write_text('[{"date": "2026-08-01", "amount": 100.0}]')
budget_file = tmp_path / "budgets.json"
budget_file.write_text('{"overall": 5000.0, "categories": []}')
svc = ForecastDataService(data_dir=tmp_path)
```

## Versioning

These files are **source assets** (commit to git). They represent the canonical spend/budget data for demos and tests.

For production, replace with a real data source (database, BI tool export, etc.) and swap `ForecastDataService` implementation.