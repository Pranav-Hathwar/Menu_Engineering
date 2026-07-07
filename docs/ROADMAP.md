# MenuMind — Roadmap & Liability Register

Honest status of the product and what to build next. Updated on the
`feature/data-integrity-and-mgmt` branch.

## Shipped on this branch

- **Duplicate-upload guard** — every upload is sha256-hashed; an identical file
  re-uploaded to the same restaurant is rejected (HTTP 409) to stop revenue
  double-counting. Explicit "Upload anyway" override available.
- **Batch tracking + delete** — each ingestion is a first-class `UploadBatch`
  record. List and delete uploads (owner-scoped, cascades sales rows). Legacy
  uploads are backfilled so pre-existing data is manageable too.
- **Classification robustness** — quadrant thresholds now use the **median**
  (resists a single high-margin outlier) and exclude sparsely-sampled items
  (< 3 units) from the threshold math.
- **Secret hygiene** — with `DEBUG` off the backend refuses to start unless
  `SECRET_KEY` is a strong (≥32-char) non-placeholder value; docker-compose now
  requires it from the host env.
- **Dashboard date-range filter + CSV export** of the daily breakdown.
- **Accurate date parsing** — the ingester now auto-detects day-first
  (DD/MM/YYYY) vs month-first columns, never lets `dayfirst` mangle ISO dates,
  converts Excel serial day numbers, and defaults unreadable dates to the
  file's most common date (reported as `dates_defaulted`) instead of "today".
- **`/api/analytics/trends`** — daily revenue with a 7-day moving average,
  weekday performance profile, Pareto revenue-concentration table, and a
  last-7-days vs prior-7-days comparison (anchored on the newest data date).
- **Week-over-week comparison cards + trend & weekday charts** on the Dashboard.
- **Price/margin what-if simulator** on the Insights page — pick an item, move
  the price ±20%, choose a demand-sensitivity preset (elasticity −0.5/−1.0/−1.5),
  see projected revenue and profit impact.
- **Margin metrics** — classification now returns `total_profit` and
  `profit_margin` (%); the Catalog shows Margin % and exports filtered CSV.
- **Robust trend detection** — insights compare first-half vs second-half
  average daily revenue (not just two arbitrary endpoint days), plus a new
  "Revenue concentration risk" (Pareto) insight.
- **Bug fixes** — Catalog/Raw Data no longer show an infinite skeleton when no
  restaurant exists; a failed login no longer hard-reloads the page and wipes
  the error; deleting a restaurant's last batch now reselects a valid
  restaurant instead of pointing at a ghost.

- **Recipe / ingredient-level COGS** — per-restaurant ingredient price list +
  bill-of-materials per menu item (`/api/recipes`). When an item has a recipe,
  every analytics calculation (classification, daily profit, trends, insights,
  recommendations) uses the live recipe cost instead of the flat uploaded
  `unit_cost`; classification reports `cost_source: recipe|upload`. New
  "Recipes & Costs" page with an ingredient manager and recipe builder;
  recipe-costed items are badged in the Catalog.

## Next features (priority order)

1. **Edit individual rows / items** — currently only whole-batch delete exists.
2. **Per-item demand forecasting** — extend the 7-day moving average to
   item-level projections.
3. **POS integrations** (Square / Toast / Petpooja) to remove manual CSV upload.
4. **Roles & sharing** — owner vs staff within one restaurant workspace.
5. **Scheduled email/PDF reports.**

## Remaining liabilities (not yet fixed)

- **JWT in `localStorage`** — XSS-stealable. Move to an httpOnly, SameSite
  cookie; add refresh tokens + server-side revocation.
- **No Alembic migrations** — schema is created/patched at runtime
  (`schema_service.ensure_runtime_schema`). Fine for dev, unsafe for prod
  schema changes. Introduce Alembic before any managed deployment.
- **`unit_cost` semantics unvalidated** — if a file provides total cost instead
  of per-unit, profit is silently wrong. Add a sanity check / column hint.
- **Committed fixtures/binaries** — `menumind_test_june2026.csv` and the
  methodology PDF live in git history; consider Git LFS or an external asset
  store if they grow.
- **No observability** — add structured logs + request metrics + error tracking.
- **SQLite for app DB** — migrate to managed Postgres for any real load.
