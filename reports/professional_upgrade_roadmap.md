# Professional Upgrade Roadmap

This roadmap is preparatory only. It was not implemented during Step 39.

## P0 — Critical Correctness

- Resolve and unit-test forecast-boundary continuity before the next forecast refresh. Reconcile the recursive engine's target rolling/return/volatility alignment with the original feature-engineering convention.
- Decide whether the 8.246098% first-step drop is accepted model behavior after the feature-alignment investigation or an implementation defect.
- Add automated checks that compare recursive feature construction against a hand-verified boundary row.
- Preserve the current frozen forecast until an explicit methodology review approves any change.

## P1 — Product Quality

- Add a compact `DATA INTEGRITY / VERIFIED` panel covering chronological validation, untouched test set, no target leakage, no future actual IBJA/market data, training-fitted preprocessing, and frozen forecast status.
- Improve the model comparison presentation with explicit source/period labels and the canonical regressor names.
- Make API connection status reflect the actual `/health` response instead of a static connected label.
- Keep loading, API-error, and partial-data states explicit and consistent across pages.

## P2 — Explainability

- Add a future `Prediction Drivers` section using the saved Linear Regression coefficients and fitted feature names.
- Show signed coefficients and absolute magnitude, while clearly distinguishing model association from causation.
- Add per-prediction contribution views using transformed feature value multiplied by coefficient, with imputation and unit caveats.
- Do not invent feature importance for Linear Regression.

## P3 — UX Polish

- Add an interactive forecast timeline with clear actual/forecast boundary and Sunday reference annotation.
- Add a What-if Analysis section using only the existing sensitivity artifact and label every value as `SCENARIO ANALYSIS`, not a model forecast.
- Improve responsive table affordances and chart accessibility descriptions.
- Add subtle page-level transitions and more explicit empty states where data is legitimately unavailable.

## P4 — Deployment Engineering

- Add automated backend endpoint and artifact-consistency tests.
- Add frontend integration and responsive smoke tests.
- Move the API base URL into environment configuration for development and production.
- Add production server settings and local virtual environment deployment setup.
- Add deployment automation, health monitoring, logging, and artifact version tracking.

## Current Gate

Step 39 identified no blocking API or frontend runtime failure. The application is functionally ready for deployment review, but the forecast-boundary feature-construction finding should be resolved or explicitly accepted before changing or refreshing the forecast package.
