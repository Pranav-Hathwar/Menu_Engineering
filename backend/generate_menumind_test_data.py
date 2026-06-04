"""Generate a realistic 1-month restaurant sales dataset for testing MenuMind.

Produces ``menumind_test_june2026.csv`` covering all 30 days of June 2026 for a
20-item menu that is deliberately engineered so that MenuMind's analytics engine
classifies the items into a clean 5 / 5 / 5 / 5 split across the four
menu-engineering quadrants (Stars, Plowhorses, Puzzles, Dogs).

IMPORTANT — how this dataset is tuned
-------------------------------------
MenuMind's engine (``app/services/analytics_service.py``) classifies on
*absolute profit per unit* in rupees, NOT on margin percentage:

    profit_per_unit   = total_revenue/total_qty - total_cost/total_qty
    avg_profitability = mean(profit_per_unit across valid items)        # threshold
    high_profitability = item.profit >= avg_profitability

Under absolute profit-per-unit, a cheap high-volume item (e.g. a Rs 60 naan) can
never out-earn an expensive Puzzle item (e.g. a Rs 750 salmon) on a per-unit
basis, so cheap items cannot be "Stars". The Star quadrant therefore uses
genuinely high-absolute-profit mains (Rs ~340-420 with fat margins) so the real
engine produces a true 5/5/5/5 split.

Two header/format notes that exercise MenuMind's ingestion:
  * The date column is written as ``order_date`` (not ``date``) to test the
    engine's column-discovery aliasing. ``_normalize_token("order_date")`` ->
    ``"orderdate"`` which is a registered alias in HEADER_KEYWORDS["date"].
  * A handful of intentionally dirty rows (qty 0, revenue 0, item "Total", ...)
    are injected to verify the validity gate rejects them.

Run directly:  python generate_menumind_test_data.py
"""

from __future__ import annotations

import csv
import random
import re
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42
OUTPUT_PATH = Path(__file__).resolve().parent / "menumind_test_june2026.csv"

# Final CSV columns. The date column intentionally uses the ``order_date`` alias
# to exercise MenuMind's column discovery.
DATE_COLUMN = "order_date"
COLUMNS = [DATE_COLUMN, "item_name", "quantity", "revenue", "unit_cost"]

YEAR, MONTH = 2026, 6  # June 2026, all 30 days

# Mirror of MenuMind's junk-name gate (app/services/upload_service.py).
JUNK_ITEM_NAMES = {"", "nan", "none", "null", "total", "subtotal", "grandtotal", "summary"}


# (item_name, unit_price, unit_cost, expected_category)
# Volume tier is implied by the category and resolved in DAILY_VOLUME below.
MENU = [
    # ---- STARS: high volume AND high absolute profit/unit -----------------
    ("Paneer Butter Masala", 320, 95, "Star"),   # profit 225
    ("Chicken Biryani",      380, 120, "Star"),   # profit 260
    ("Mutton Rogan Josh",    420, 150, "Star"),   # profit 270
    ("Tandoori Chicken",     360, 120, "Star"),   # profit 240
    ("Paneer Tikka Masala",  340, 110, "Star"),   # profit 230
    # ---- PLOWHORSES: high volume BUT low absolute profit/unit -------------
    ("Veg Fried Rice",       200, 140, "Plowhorse"),  # profit 60
    ("Masala Papad",          50,  38, "Plowhorse"),  # profit 12
    ("Plain Lassi",           80,  58, "Plowhorse"),  # profit 22
    ("Steam Rice",            90,  68, "Plowhorse"),  # profit 22
    ("Gulab Jamun",           80,  60, "Plowhorse"),  # profit 20
    # ---- PUZZLES: low volume BUT high absolute profit/unit ----------------
    ("Truffle Pasta",        550, 140, "Puzzle"),  # profit 410
    ("Grilled Salmon",       750, 220, "Puzzle"),  # profit 530
    ("Cheese Burst Pizza",   480, 130, "Puzzle"),  # profit 350
    ("Belgian Waffle",       320,  80, "Puzzle"),  # profit 240
    ("Mango Cheesecake",     280,  65, "Puzzle"),  # profit 215
    # ---- DOGS: low volume AND low absolute profit/unit --------------------
    ("Veg Sandwich",         120,  95, "Dog"),  # profit 25
    ("Plain Khichdi",        100,  78, "Dog"),  # profit 22
    ("Buttermilk",            40,  30, "Dog"),  # profit 10
    ("Jeera Rice",           130, 105, "Dog"),  # profit 25
    ("Papad Fry",             45,  36, "Dog"),  # profit 9
]

# Base daily unit ranges per category (inclusive). Weekend uplift applies to the
# high-traffic categories only.
DAILY_VOLUME = {
    "Star":      {"low": 15, "high": 30, "weekend_uplift": True},
    "Plowhorse": {"low": 12, "high": 25, "weekend_uplift": True},
    "Puzzle":    {"low": 2,  "high": 6,  "weekend_uplift": False},
    "Dog":       {"low": 1,  "high": 4,  "weekend_uplift": False},
}

WEEKEND_MULTIPLIER = 1.20  # +20% on Sat/Sun


def _normalize_token(value) -> str:
    """Mirror of MenuMind's token normalizer (used for the junk-name gate)."""
    return re.sub(r"[^a-z0-9#]+", "", str(value).strip().lower())


def _june_days() -> list[date]:
    start = date(YEAR, MONTH, 1)
    return [start + timedelta(days=offset) for offset in range(30)]


def _daily_quantity(rng: random.Random, category: str, day: date) -> int:
    """Sample one day's unit volume with weekend uplift and +/-15% noise."""
    spec = DAILY_VOLUME[category]
    base = rng.randint(spec["low"], spec["high"])

    if spec["weekend_uplift"] and day.weekday() >= 5:  # 5=Sat, 6=Sun
        base *= WEEKEND_MULTIPLIER

    noise_factor = rng.uniform(0.85, 1.15)  # +/-15% uniform noise
    quantity = round(base * noise_factor)
    return max(1, quantity)


def _build_rows(rng: random.Random) -> list[dict]:
    """One row per (item, day): 20 items x 30 days = 600 clean rows."""
    rows: list[dict] = []
    for day in _june_days():
        for item_name, unit_price, unit_cost, category in MENU:
            quantity = _daily_quantity(rng, category, day)
            rows.append(
                {
                    DATE_COLUMN: day.isoformat(),
                    "item_name": item_name,
                    "quantity": quantity,
                    "revenue": unit_price * quantity,  # total revenue for the row
                    "unit_cost": unit_cost,            # COGS per single unit
                }
            )
    return rows


def _dirty_rows() -> list[dict]:
    """Rows MenuMind's validity gate must reject (junk name / qty 0 / rev 0)."""
    return [
        {DATE_COLUMN: "2026-06-10", "item_name": "Total",       "quantity": 0,  "revenue": 0,     "unit_cost": 0},
        {DATE_COLUMN: "2026-06-17", "item_name": "Subtotal",    "quantity": 0,  "revenue": 18450, "unit_cost": 0},
        {DATE_COLUMN: "2026-06-23", "item_name": "",            "quantity": 7,  "revenue": 0,     "unit_cost": 20},
        {DATE_COLUMN: "2026-06-28", "item_name": "GRAND TOTAL", "quantity": 0,  "revenue": 0,     "unit_cost": 0},
    ]


def _inject_dirty_rows(rng: random.Random, rows: list[dict]) -> list[dict]:
    """Splice the dirty rows in at random positions among the clean rows."""
    combined = list(rows)
    for dirty in _dirty_rows():
        position = rng.randint(0, len(combined))
        combined.insert(position, dirty)
    return combined


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Validation: reload the CSV and reproduce MenuMind's classification exactly.
# ---------------------------------------------------------------------------

def classify_from_csv(path: Path) -> tuple[list[dict], float, float]:
    """Load the CSV back and replicate analytics_service.get_menu_engineering_classification.

    Returns (classified_items, avg_popularity, avg_profitability).
    """
    df = pd.read_csv(path)

    # Validity gate identical to MenuMind: drop junk names, qty<=0, revenue<=0.
    df = df.rename(columns={DATE_COLUMN: "date"})
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)
    df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce").fillna(0.0)

    valid_mask = (
        df["item_name"].map(lambda v: _normalize_token(v) not in JUNK_ITEM_NAMES)
        & (df["revenue"] > 0)
        & (df["quantity"] > 0)
    )
    clean = df[valid_mask]

    # Per-item aggregates: Qi, Ri, Ci (Ci = sum of unit_cost * quantity).
    grouped = clean.groupby("item_name").apply(
        lambda g: pd.Series(
            {
                "total_quantity": g["quantity"].sum(),
                "total_revenue": g["revenue"].sum(),
                "total_cost": (g["unit_cost"] * g["quantity"]).sum(),
            }
        ),
        include_groups=False,
    ).reset_index()

    items = []
    for _, row in grouped.iterrows():
        qty = float(row["total_quantity"])
        rev = float(row["total_revenue"])
        cogs = float(row["total_cost"])
        profit_per_unit = (rev / qty) - (cogs / qty)  # Ri/Qi - Ci/Qi
        items.append(
            {
                "item_name": row["item_name"],
                "total_quantity": qty,
                "profit": profit_per_unit,
            }
        )

    # Mirror analytics_service: median thresholds over adequately-sampled items.
    from statistics import median

    MIN_CLASSIFY_QUANTITY = 3
    sample = [i for i in items if i["total_quantity"] >= MIN_CLASSIFY_QUANTITY] or items
    avg_popularity = median(i["total_quantity"] for i in sample)
    avg_profitability = median(i["profit"] for i in sample)

    for item in items:
        high_pop = item["total_quantity"] >= avg_popularity
        high_profit = item["profit"] >= avg_profitability
        if high_pop and high_profit:
            item["category"] = "Star"
        elif high_pop:
            item["category"] = "Plowhorse"
        elif high_profit:
            item["category"] = "Puzzle"
        else:
            item["category"] = "Dog"

    return items, avg_popularity, avg_profitability


def validate(path: Path) -> None:
    items, avg_popularity, avg_profitability = classify_from_csv(path)
    expected = {name: category for name, _, _, category in MENU}

    by_name = {item["item_name"]: item for item in items}

    print("\n" + "=" * 84)
    print("MenuMind classification (reproduced from the generated CSV)")
    print("=" * 84)
    print(f"avg_popularity threshold (units)     : {avg_popularity:8.1f}")
    print(f"avg_profitability threshold (Rs/unit): {avg_profitability:8.1f}")
    print("-" * 84)
    print(f"{'Item':<24}{'Units':>8}{'Profit/u':>10}  {'Predicted':<11}{'Expected':<11}{'OK'}")
    print("-" * 84)

    mismatches = []
    order = {"Star": 0, "Plowhorse": 1, "Puzzle": 2, "Dog": 3}
    for name in sorted(expected, key=lambda n: (order[expected[n]], n)):
        item = by_name.get(name)
        if item is None:
            mismatches.append(f"{name}: missing from classified output (was it rejected?)")
            print(f"{name:<24}{'--':>8}{'--':>10}  {'MISSING':<11}{expected[name]:<11}X")
            continue
        predicted = item["category"]
        ok = predicted == expected[name]
        if not ok:
            mismatches.append(
                f"{name}: predicted '{predicted}' but expected '{expected[name]}' "
                f"(units={item['total_quantity']:.0f}, profit/u={item['profit']:.1f})"
            )
        print(
            f"{name:<24}{item['total_quantity']:>8.0f}{item['profit']:>10.1f}  "
            f"{predicted:<11}{expected[name]:<11}{'Y' if ok else 'X'}"
        )

    # Quadrant tallies.
    counts = {"Star": 0, "Plowhorse": 0, "Puzzle": 0, "Dog": 0}
    for item in items:
        counts[item["category"]] += 1
    print("-" * 84)
    print(f"Quadrant counts: {counts}")
    print("=" * 84)

    # Assertions ------------------------------------------------------------
    if mismatches:
        raise AssertionError(
            "Menu-engineering classification did not match the intended quadrants:\n  - "
            + "\n  - ".join(mismatches)
        )

    for category in ("Star", "Plowhorse", "Puzzle", "Dog"):
        if counts[category] != 5:
            raise AssertionError(
                f"Expected exactly 5 {category}s but engine produced {counts[category]}. "
                f"Full tally: {counts}"
            )

    print("All 20 items landed in their intended quadrant (5 Stars / 5 Plowhorses / "
          "5 Puzzles / 5 Dogs). OK")


def main() -> None:
    rng = random.Random()
    random.seed(SEED)
    rng.seed(SEED)

    clean_rows = _build_rows(rng)
    all_rows = _inject_dirty_rows(rng, clean_rows)
    write_csv(all_rows, OUTPUT_PATH)

    clean_count = len(clean_rows)
    dirty_count = len(all_rows) - clean_count
    print(f"Wrote {len(all_rows)} rows ({clean_count} clean + {dirty_count} dirty) to CSV.")

    validate(OUTPUT_PATH)

    print(f"\nOutput CSV: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
