# Changelog: EPMCDMETST-59936

_Generated: 2026-08-14_

## Overview
Display forecast chart overlay with expected month-end totals and risk flags

## Changes
Implements EPMCDMETST-59936.
- [ ] Feature: Forecast chart overlay — actual spend + projected month-end line (FR-1)
- [ ] Feature: Risk flags on budget exceedance (overall & per-category) (FR-2)
- [ ] Feature: Overall/category view toggle (FR-3)
- [ ] Feature: Graceful degradation when budgets absent — risk flags hidden, notice shown (FR-4)
- [ ] Feature: Client-side period cache (in-memory Map, no sessionStorage) (NFR-2)
- [ ] Feature: API key authentication on /api/spend/* endpoints (design review revision)
- [ ] Feature: uPlot CDN bundle strategy (~40 KB) for 2-second render target (NFR-1)
- [ ] Feature: Accessible risk flag marker (role=alert, aria-label) and keyboard-accessible view toggle (NFR-3)

## Known Limitations
- Per-category spend projections currently reflect overall spend data; category-scoped projection will be wired to per-category records in a follow-up story
- The 2-second render target (NFR-1) is validated manually via Lighthouse; automated performance gating is deferred to v1.1
- The forecast API server must be started separately (`python -m documentation_sync.spend_api_router`); integration with the main `docsync` CLI entry point is deferred