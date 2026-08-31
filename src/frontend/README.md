# ForecastChart Frontend

Zero-build frontend for visualizing spend forecasts. Uses **uPlot** (via CDN) for lightweight, fast charting.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Main page: chart, view toggle, period selector, refresh button, risk flag, budget notice |
| `ForecastChart.js` | uPlot chart component; fetches `/api/spend/forecast`, renders actual + projected bars |
| `view_toggle.js` | Overall/Category view switcher; populates from `/api/spend/budgets` |
| `period_cache.js` | In-memory cache keyed by `period:category`; invalidated by Refresh button |
| `risk_flag_marker.js` | Renders server-provided risk flag (triggered/label); **no threshold logic in frontend** |
| `budget_absence_notice.js` | Shows "No budget configured — risk flags unavailable" when budget is null (FR-4) |

## Quick Start

```bash
# Terminal 1: Start API server
python -m documentation_sync.spend_api_router
# → Runs on http://127.0.0.1:5050

# Terminal 2: Serve frontend (any static server)
npx serve src/frontend
# or
python -m http.server -d src/frontend 8080
# → Open http://localhost:8080
```

Default period: `2026-08` (matches sample `data/spend_records.json`).

## Architecture

### Data Flow

```
index.html
  └─→ ForecastChart.load(period, category)
        └─→ fetch(`${API_BASE}/api/spend/forecast?period=...&category=...`)
              └─→ period_cache.getOrFetch(key, fetcher)
                    └─→ ForecastChart.render(data)
                          └─→ uPlot.update() → chart DOM
```

### Risk Flag (FR-2, FR-4)

- **Server-side only**: `risk_flag_evaluator.py` compares `projected_total > budget`
- **Frontend receives**: `{ triggered: boolean, label: string }` or `null`
- **No threshold math in JS** — enforced by design review

### Cache Invalidation (FR-5)

- `period_cache.js` stores responses keyed by `"${period}:${category || 'overall'}"`
- **Refresh button** → `cache.invalidate(key)` → next load re-fetches
- **Period change** → new key → cache miss → fetch

### View Toggle (FR-3)

- `view_toggle.js` fetches `/api/spend/budgets` on load
- Populates category buttons from `categories[]`
- Click → calls `chart.load(period, categoryId)` or `chart.load(period, null)` for overall

## Configuration

Edit the inline script in `index.html`:

```javascript
const API_BASE = "http://127.0.0.1:5050";  // Change for production
const API_KEY  = null;                       // Set to match SPEND_API_KEY env var
```

For production:
- Set `SPEND_API_KEY` on the API server
- Set `API_KEY` in frontend to the same value
- Serve frontend via HTTPS; API on same origin or with CORS

## uPlot Details

- **Version**: 1.6.31 (via jsDelivr CDN)
- **Bundle size**: ~40 KB gzipped
- **Why uPlot**: Tiny, fast, no dependencies, good for time-series bars

Chart config (in `ForecastChart.js`):
- Series: actual spend (bars), projected total (single bar at month-end)
- X-axis: days 1..N of month
- Y-axis: currency
- Tooltip: date + amount

## Adding Features

### New Chart Type
1. Extend `ForecastChart.render()` with new series/options
2. Update uPlot config in `createChart()`

### New API Endpoint
1. Add route in `spend_api_router.py`
2. Add fetch call in relevant component
3. Update cache key strategy if needed

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Chart empty | Check browser console → Network tab → `/api/spend/forecast` response |
| "Failed to load budgets" | API server not running or wrong `API_BASE` |
| Risk flag not showing | Verify `budgets.json` has `overall` or `categories[].budget` |
| Cache not clearing | Refresh button calls `cache.invalidate()`; check `period_cache.js` |
| CORS errors | Run API on same origin, or add CORS headers in Flask |

## Design Review Decisions

| Decision | Rationale |
|----------|-----------|
| uPlot over Chart.js/Recharts | Bundle size (40 KB vs 200+ KB), no build step |
| Server-side risk eval | Security: thresholds not exposed; single source of truth |
| In-memory cache only | Simplicity; Refresh button handles staleness |
| No framework (React/Vue) | Zero build, single HTML file, easy to embed |