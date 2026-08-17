# Architecture: EPMCDMETST-59936

## Overview
A file-based Python engine reads a story, builds structured requirements, and renders Markdown documentation artifacts via templated generators.

## Components
- `parser`: loads JSON/Markdown story input
- `validator`: enforces required fields and traceability rules
- `generator`: builds requirements and downstream docs
- `cli`: orchestrates the end-to-end flow

## Requirements Addressed
- FR-1: Chart shows actual spend to date and projected month-end line for selected period.
- FR-2: Risk flags appear when projection exceeds overall or category budget (when budgets exist).
- FR-3: User can switch between overall and category views.
- FR-4: When budgets are absent, risk flags are hidden and UI indicates budgets are required for risk.
- FR-5: UI renders within 2 seconds on typical client devices.
- FR-6: Chart data requests are cached per period to reduce repeated calls.
