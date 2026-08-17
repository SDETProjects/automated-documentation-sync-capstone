# EPMCDMETST-59936: Display forecast chart overlay with expected month-end totals and risk flags

_Fetched: 2026-08-14_

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


## Acceptance Criteria
- Chart shows actual spend to date and projected month-end line for selected period.
- Risk flags appear when projection exceeds overall or category budget (when budgets exist).
- User can switch between overall and category views.
- When budgets are absent, risk flags are hidden and UI indicates budgets are required for risk.
- UI renders within 2 seconds on typical client devices.
- Chart data requests are cached per period to reduce repeated calls.

## Metadata
| Field | Value |
|-------|-------|
| Priority | Low |
| Reporter | Sathyapriya_Mohan@epam.com |
