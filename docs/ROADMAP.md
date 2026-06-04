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

## Next features (priority order)

1. **Period comparison** — "this month vs last": % deltas on revenue, profit,
   units. The daily endpoint already returns the data; needs a compare view.
2. **Price-change / margin simulator** — "raise item X by 10% → projected profit
   impact". This is the highest-value decision feature.
3. **Recipe / ingredient-level COGS** — replace the flat `unit_cost` with a small
   bill-of-materials so cost is accurate when ingredient prices move.
4. **Edit individual rows / items** — currently only whole-batch delete exists.
5. **Demand forecasting** — start with a 7-day moving average per item.
6. **POS integrations** (Square / Toast / Petpooja) to remove manual CSV upload.
7. **Roles & sharing** — owner vs staff within one restaurant workspace.
8. **Scheduled email/PDF reports.**

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
