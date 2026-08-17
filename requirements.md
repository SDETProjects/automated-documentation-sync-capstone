# Requirements: EPMCDMETST-59936

_Generated: 2026-08-14_

## Story Summary
Display forecast chart overlay with expected month-end totals and risk flags

## Description
As a user, I want a forecast overlay on charts so that I can visually compare actual spend vs projected month-end totals and see risk flags.

Acceptance Criteria:
1. Chart shows actual spend to date and projected month-end line for selected period.
2. Risk flags appear when projection exceeds overall or category budget (when budgets exist).
3. User can switch between overall and category views.
4. When budgets are absent, risk flags are hidden and UI indicates budgets are required for risk.

Non-Functional Requirements:
- UI renders within 2 seconds on typical client devices.
- Chart data requests are cached per period to reduce repeated calls.


## Traceability Matrix
| ID | Category | Requirement | Source |
|----|----------|-------------|--------|
| US-1 | US | Display forecast chart overlay with expected month-end totals and risk flags (EPMCDMETST-59936) | EPMCDMETST-59936 |
| FR-1 | FR | Chart shows actual spend to date and projected month-end line for selected period. | EPMCDMETST-59936 |
| FR-2 | FR | Risk flags appear when projection exceeds overall or category budget (when budgets exist). | EPMCDMETST-59936 |
| FR-3 | FR | User can switch between overall and category views. | EPMCDMETST-59936 |
| FR-4 | FR | When budgets are absent, risk flags are hidden and UI indicates budgets are required for risk. | EPMCDMETST-59936 |
| FR-5 | FR | UI renders within 2 seconds on typical client devices. | EPMCDMETST-59936 |
| FR-6 | FR | Chart data requests are cached per period to reduce repeated calls. | EPMCDMETST-59936 |
| NFR-1 | NFR | Every generated artifact must retain traceability back to the originating story EPMCDMETST-59936 via requirement IDs. | EPMCDMETST-59936 |

## Clarifications
None identified.
