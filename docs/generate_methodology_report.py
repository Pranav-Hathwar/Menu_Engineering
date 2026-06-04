"""
generate_methodology_report.py

Builds a clean, paper-style PDF that documents the exact profit-calculation
and menu-engineering classification logic used by the MenuMind / Menu
Engineering application. Diagrams are drawn natively with matplotlib and the
whole document is written through matplotlib's PdfPages, so the only
dependency is matplotlib.

Run:  python docs/generate_methodology_report.py
Output: docs/MenuMind_Methodology.pdf
"""

from __future__ import annotations

import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

# ----------------------------------------------------------------------------
# Palette + page geometry
# ----------------------------------------------------------------------------
PAGE_W, PAGE_H = 8.27, 11.69          # A4 portrait, inches
MARGIN_L, MARGIN_R = 0.09, 0.91        # axes-fraction left / right text column

INK = "#1f2933"
MUTED = "#52606d"
FAINT = "#9aa5b1"
RULE = "#cbd2d9"
ACCENT = "#2563eb"

STAR = "#059669"
PLOW = "#d97706"
PUZZLE = "#2563eb"
DOG = "#dc2626"
BOXBG = "#f4f6f8"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "pdf.fonttype": 42,          # embed TrueType so the paper is selectable text
    "text.color": INK,
})


# ----------------------------------------------------------------------------
# Low-level page helpers
# ----------------------------------------------------------------------------
def new_page(pdf):
    fig = plt.figure(figsize=(PAGE_W, PAGE_H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def footer(ax, page_no):
    ax.plot([MARGIN_L, MARGIN_R], [0.045, 0.045], color=RULE, lw=0.8)
    ax.text(MARGIN_L, 0.028, "MenuMind  ·  Menu-Engineering Methodology",
            fontsize=7.5, color=FAINT)
    ax.text(MARGIN_R, 0.028, f"{page_no}", fontsize=7.5, color=FAINT, ha="right")


def close(pdf, fig, ax, page_no):
    footer(ax, page_no)
    pdf.savefig(fig)
    plt.close(fig)


class Cursor:
    """Tiny vertical-flow text engine in axes-fraction coordinates."""
    def __init__(self, ax, y=0.93):
        self.ax = ax
        self.y = y

    def gap(self, dy):
        self.y -= dy

    def h1(self, text):
        self.ax.text(MARGIN_L, self.y, text, fontsize=17, fontweight="bold",
                     color=INK, va="top")
        self.y -= 0.028
        self.ax.plot([MARGIN_L, MARGIN_R], [self.y, self.y], color=ACCENT, lw=1.6)
        self.y -= 0.022

    def h2(self, text):
        self.gap(0.006)
        self.ax.text(MARGIN_L, self.y, text, fontsize=12.5, fontweight="bold",
                     color=ACCENT, va="top")
        self.y -= 0.026

    def body(self, text, color=MUTED, size=9.6, lh=0.0185, width=104, indent=0.0):
        for para in text.split("\n"):
            if para.strip() == "":
                self.y -= lh
                continue
            for line in textwrap.wrap(para, width=width):
                self.ax.text(MARGIN_L + indent, self.y, line, fontsize=size,
                             color=color, va="top")
                self.y -= lh
        self.y -= 0.004

    def bullet(self, label, text, color=MUTED, size=9.6, lh=0.0185, width=92):
        self.ax.text(MARGIN_L + 0.012, self.y, "•", fontsize=size, color=ACCENT, va="top")
        first = True
        head = f"{label}  " if label else ""
        wrapped = textwrap.wrap(head + text, width=width)
        for line in wrapped:
            self.ax.text(MARGIN_L + 0.032, self.y, line, fontsize=size,
                         color=color, va="top")
            self.y -= lh
            first = False
        self.y -= 0.003

    def formula(self, text, size=11):
        box = FancyBboxPatch((MARGIN_L, self.y - 0.030), MARGIN_R - MARGIN_L, 0.040,
                             boxstyle="round,pad=0.004,rounding_size=0.006",
                             linewidth=0, facecolor=BOXBG,
                             transform=self.ax.transData)
        self.ax.add_patch(box)
        self.ax.text((MARGIN_L + MARGIN_R) / 2, self.y - 0.010, text,
                     fontsize=size, color=INK, ha="center", va="center")
        self.y -= 0.058

    def note(self, text):
        box = FancyBboxPatch((MARGIN_L, self.y - 0.001), MARGIN_R - MARGIN_L, 0.001,
                             boxstyle="round", linewidth=0, facecolor="none")
        self.ax.add_patch(box)
        self.ax.text(MARGIN_L + 0.006, self.y, "▍", fontsize=9.5, color=ACCENT, va="top")
        for line in textwrap.wrap(text, width=98):
            self.ax.text(MARGIN_L + 0.028, self.y, line, fontsize=9.0,
                         color=MUTED, va="top", style="italic")
            self.y -= 0.0175
        self.y -= 0.006


# ----------------------------------------------------------------------------
# PAGE 1 — Title
# ----------------------------------------------------------------------------
def page_title(pdf):
    fig, ax = new_page(pdf)

    ax.add_patch(Rectangle((0, 0.78), 1, 0.22, color="#0f172a"))
    ax.text(0.5, 0.905, "MenuMind", fontsize=34, fontweight="bold",
            color="white", ha="center")
    ax.text(0.5, 0.845, "A Quantitative Methodology for Menu Profitability\nand Engineering Classification",
            fontsize=12.5, color="#c7d2fe", ha="center", linespacing=1.5)

    ax.text(0.5, 0.70,
            "How item-level profit is computed and how each dish is\n"
            "classified as a Star, Plowhorse, Puzzle, or Dog.",
            fontsize=12, color=MUTED, ha="center", linespacing=1.6)

    # Mini 2x2 emblem
    cx, cy, s = 0.5, 0.45, 0.14
    quads = [
        (cx - s, cy,      STAR,   "Star"),
        (cx,     cy,      PLOW,   "Plowhorse"),
        (cx - s, cy - s,  PUZZLE, "Puzzle"),
        (cx,     cy - s,  DOG,    "Dog"),
    ]
    for x, y, c, label in quads:
        ax.add_patch(FancyBboxPatch((x, y), s, s,
                     boxstyle="round,pad=0.002,rounding_size=0.01",
                     linewidth=0, facecolor=c, alpha=0.92))
        ax.text(x + s / 2, y + s / 2, label, fontsize=10.5, color="white",
                ha="center", va="center", fontweight="bold")
    ax.annotate("", xy=(cx - s - 0.02, cy + s + 0.02), xytext=(cx - s - 0.02, cy - s),
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))
    ax.text(cx - s - 0.035, cy, "Profitability", rotation=90, fontsize=9,
            color=MUTED, ha="center", va="center")
    ax.annotate("", xy=(cx + s + 0.02, cy - s - 0.02), xytext=(cx - s, cy - s - 0.02),
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))
    ax.text(cx, cy - s - 0.045, "Popularity (units sold)", fontsize=9,
            color=MUTED, ha="center", va="center")

    ax.plot([MARGIN_L, MARGIN_R], [0.16, 0.16], color=RULE, lw=0.8)
    ax.text(MARGIN_L, 0.13, "Technical Methodology Report", fontsize=10.5,
            fontweight="bold", color=INK)
    ax.text(MARGIN_L, 0.108, "Derived directly from the production analytics engine.",
            fontsize=8.6, color=MUTED)
    ax.text(MARGIN_R, 0.13, "Version 1.0", fontsize=9, color=MUTED, ha="right")
    ax.text(MARGIN_R, 0.108, "June 2026", fontsize=9, color=MUTED, ha="right")

    pdf.savefig(fig)
    plt.close(fig)


# ----------------------------------------------------------------------------
# PAGE 2 — Abstract + pipeline overview
# ----------------------------------------------------------------------------
def page_overview(pdf, page_no):
    fig, ax = new_page(pdf)
    c = Cursor(ax)

    c.h1("1.  Overview")
    c.body(
        "MenuMind turns a raw restaurant sales export into an item-level "
        "profitability map. The system never asks the operator to pre-compute "
        "anything: it ingests whatever spreadsheet the point-of-sale produced, "
        "infers which columns mean what, reduces every transaction to four "
        "numbers per dish, and then places each dish into one of four strategic "
        "categories using the classical menu-engineering matrix of Kasavana & "
        "Smith (1982).")
    c.body(
        "This report documents the complete chain of logic — from a messy CSV "
        "row to a Star/Plowhorse/Puzzle/Dog verdict and an actionable "
        "recommendation — exactly as implemented in the codebase. Every formula "
        "below corresponds to a concrete line in the analytics engine.")

    c.gap(0.012)
    c.h2("Processing pipeline at a glance")

    # Pipeline diagram
    stages = [
        ("Raw upload\n(CSV / XLSX / JSON)", "#0f172a"),
        ("Header &\ncolumn discovery", ACCENT),
        ("Per-row\nnormalization", ACCENT),
        ("Aggregate\nper item", STAR),
        ("Profit &\nthresholds", STAR),
        ("Classify +\nrecommend", DOG),
    ]
    n = len(stages)
    bx0, bx1 = MARGIN_L, MARGIN_R
    bw = (bx1 - bx0) / n
    by = 0.585
    bh = 0.060
    for i, (label, col) in enumerate(stages):
        x = bx0 + i * bw
        ax.add_patch(FancyBboxPatch((x + 0.006, by), bw - 0.012, bh,
                     boxstyle="round,pad=0.002,rounding_size=0.006",
                     linewidth=0, facecolor=col, alpha=0.92))
        ax.text(x + bw / 2, by + bh / 2, label, fontsize=7.4, color="white",
                ha="center", va="center", fontweight="bold", linespacing=1.2)
        if i < n - 1:
            ax.annotate("", xy=(x + bw + 0.006, by + bh / 2),
                        xytext=(x + bw - 0.006, by + bh / 2),
                        arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.1))
    c.y = by - 0.03

    c.h2("The four numbers that drive everything")
    c.body(
        "After ingestion, each individual sales row is stored as exactly four "
        "analytic fields. Every downstream metric is built from these alone:")
    c.bullet("item_name —", "the dish, cleaned and title-cased so that "
             "'  MARGHERITA  pizza' and 'Margherita Pizza' aggregate together.")
    c.bullet("quantity —", "integer units sold in that row (defaults to 1 if the "
             "export has no quantity column).")
    c.bullet("revenue —", "money taken for that row, in INR. If only a unit price "
             "is present, revenue is reconstructed as price × quantity.")
    c.bullet("unit_cost —", "cost of goods (COGS) to produce one unit; defaults "
             "to 0 when the export carries no cost column.")
    c.note("Design choice: revenue is stored as a row total, while cost is stored "
           "per unit. Section 4 shows how the engine reconciles the two so that "
           "profit is always computed on a per-unit basis.")

    close(pdf, fig, ax, page_no)


# ----------------------------------------------------------------------------
# PAGE 3 — Ingestion / how items are decided
# ----------------------------------------------------------------------------
def page_ingestion(pdf, page_no):
    fig, ax = new_page(pdf)
    c = Cursor(ax)

    c.h1("2.  How Items Are Identified and Listed")
    c.body(
        "Restaurant exports are notoriously messy: title rows, merged cells, "
        "blank lines, currency symbols, and inconsistent headers. The ingestion "
        "layer is built to survive all of this without manual cleanup.")

    c.h2("2.1  Column discovery")
    c.body(
        "The engine does not trust column positions. Instead it scores headers "
        "against a keyword dictionary and maps each physical column to one of "
        "five logical roles. A header (or, if the first row is junk, the first "
        "row that scores ≥ 2 keyword hits) is promoted to the schema.")

    # keyword table
    rows = [
        ("item_name", "item, name, product, menu, dish, sku, description"),
        ("quantity", "qty, quantity, count, sold, units, orders, volume"),
        ("revenue", "revenue, sales, amount, total, gross, net, turnover, value"),
        ("unit_cost", "cost, cogs, expense, purchase, ingredient"),
        ("date", "date, time, day, businessdate, orderdate"),
    ]
    y = c.y
    ax.add_patch(Rectangle((MARGIN_L, y - 0.022), MARGIN_R - MARGIN_L, 0.022,
                 color="#0f172a"))
    ax.text(MARGIN_L + 0.012, y - 0.011, "Logical field", fontsize=8.6,
            color="white", va="center", fontweight="bold")
    ax.text(MARGIN_L + 0.20, y - 0.011, "Matched against (sample aliases)",
            fontsize=8.6, color="white", va="center", fontweight="bold")
    y -= 0.022
    for i, (field, kws) in enumerate(rows):
        bg = "#ffffff" if i % 2 else BOXBG
        ax.add_patch(Rectangle((MARGIN_L, y - 0.022), MARGIN_R - MARGIN_L, 0.022,
                     color=bg))
        ax.text(MARGIN_L + 0.012, y - 0.011, field, fontsize=8.4, color=ACCENT,
                va="center", fontweight="bold")
        ax.text(MARGIN_L + 0.20, y - 0.011, kws, fontsize=8.0, color=MUTED,
                va="center")
        y -= 0.022
    c.y = y - 0.012

    c.body(
        "Fallback heuristics handle exports with no usable headers. The item "
        "column is chosen as the most text-like column (low numeric ratio, "
        "moderate length, many distinct values); quantity is inferred as the "
        "low-magnitude numeric column; revenue as the highest-summing numeric "
        "column. This means even an unlabeled table still classifies correctly.")

    c.h2("2.2  Per-row normalization and the validity gate")
    c.body(
        "Every candidate row is cleaned and then must pass a strict gate before "
        "it is allowed to influence any metric. A row is KEPT only if all three "
        "hold:")
    c.bullet("", "item_name is not junk (not blank, 'nan', 'total', 'subtotal', "
             "'summary', etc.);")
    c.bullet("", "revenue > 0;")
    c.bullet("", "quantity > 0.")
    c.body(
        "Rows failing the gate are counted as rows_rejected and reported back to "
        "the user, but never enter the profit math. This is what keeps summary "
        "rows and refunds from polluting the averages that decide classification.")
    c.note("Net is intentionally excluded from the revenue keyword used to pick "
           "the price fallback, so a 'net' column never masquerades as unit price. "
           "Numbers are parsed by stripping every character except digits, minus, "
           "and decimal point — so 'Rs 4,000' becomes 4000 cleanly.")

    close(pdf, fig, ax, page_no)


# ----------------------------------------------------------------------------
# PAGE 4 — Profit model
# ----------------------------------------------------------------------------
def page_profit(pdf, page_no):
    fig, ax = new_page(pdf)
    c = Cursor(ax)

    c.h1("3.  The Profit Model")
    c.body(
        "All profitability is computed per menu item after aggregating every "
        "kept row for that item across the selected date range and restaurant. "
        "For an item i, the engine first sums the raw quantities, revenues, and "
        "costs:")

    c.formula(r"$Q_i = \sum q,\quad  R_i = \sum r,\quad  C_i = \sum (\mathrm{unit\_cost}\times q)$")

    c.body(
        "Note that total cost is the sum of unit_cost × quantity over the rows — "
        "cost is weighted by how many units each row sold, while revenue is "
        "already a row total. From these three sums, the engine derives "
        "per-unit economics:")

    c.formula(r"$\bar p_i=\dfrac{R_i}{Q_i}\;(\mathrm{avg\ unit\ price}),\quad"
              r"\bar c_i=\dfrac{C_i}{Q_i}\;(\mathrm{avg\ unit\ cost})$")

    c.h2("3.1  Profit per unit — the core metric")
    c.body(
        "The single most important quantity in the whole system is the average "
        "profit margin earned on one unit of the item:")

    c.formula(r"$\mathrm{profit}_i \;=\; \bar p_i - \bar c_i \;=\; "
              r"\dfrac{R_i}{Q_i}-\dfrac{C_i}{Q_i}$", size=12)

    c.body(
        "This per-unit profit — not total profit — is the value plotted on the "
        "profitability axis of the menu matrix and the number shown on every "
        "card in the dashboard ('Unit Profit: Rs ...'). Using a per-unit figure "
        "makes a low-volume, high-margin dish directly comparable to a "
        "high-volume, thin-margin dish.")

    c.h2("3.2  Gross profit contribution")
    c.body(
        "For ranking which items actually move the bottom line, the engine also "
        "computes each item's total contribution to gross profit, and sums these "
        "for the business-wide figure reported in Insights:")

    c.formula(r"$\mathrm{GP}_i=\mathrm{profit}_i\times Q_i,\qquad"
              r"\mathrm{GP}_{\mathrm{total}}=\sum_i \mathrm{GP}_i$")

    c.note("When an export carries no cost column, unit_cost defaults to 0, so "
           "profit collapses to average unit price and 'profit' should be read as "
           "gross revenue per unit. Supplying COGS is what turns the same pipeline "
           "into a true net-margin engine.")

    close(pdf, fig, ax, page_no)


# ----------------------------------------------------------------------------
# PAGE 5 — Classification + matrix diagram
# ----------------------------------------------------------------------------
def page_classification(pdf, page_no):
    fig, ax = new_page(pdf)
    c = Cursor(ax)

    c.h1("4.  Classifying Each Item")
    c.body(
        "With a per-unit profit and a unit count for every item, classification "
        "is a relative comparison against the menu's own averages. The engine "
        "computes two thresholds across the N valid items:")

    c.formula(r"$\overline{\mathrm{Pop}}=\dfrac{1}{N}\sum_i Q_i,\qquad"
              r"\overline{\mathrm{Prof}}=\dfrac{1}{N}\sum_i \mathrm{profit}_i$")

    c.body(
        "Each item is then tagged on two binary axes — is it at or above the "
        "average on popularity, and at or above the average on profitability? "
        "The four combinations give the four classic categories:")

    # Decision rules
    c.bullet("Star —", "popularity ≥ avg AND profit ≥ avg.")
    c.bullet("Plowhorse —", "popularity ≥ avg, profit < avg.")
    c.bullet("Puzzle —", "popularity < avg, profit ≥ avg.")
    c.bullet("Dog —", "popularity < avg, profit < avg.")
    c.note("The comparison is inclusive (≥): an item sitting exactly on the "
           "average is given the benefit of the doubt and counts as 'high'. "
           "Thresholds are recomputed for every query, so categories always "
           "reflect the current filter window, not a fixed historical baseline.")

    # ---- 2x2 matrix diagram ----
    c.gap(0.004)
    mx, my = 0.18, 0.085           # lower-left of matrix
    mw = 0.64
    mh = 0.30
    midx = mx + mw / 2
    midy = my + mh / 2
    cells = [
        (mx,          midy, mw/2, mh/2, PUZZLE, "PUZZLE",
         "Low demand\nHigh margin", "Promote &\nreposition"),
        (midx,        midy, mw/2, mh/2, STAR,   "STAR",
         "High demand\nHigh margin", "Protect &\nfeature"),
        (mx,          my,   mw/2, mh/2, DOG,    "DOG",
         "Low demand\nLow margin", "Rework or\nremove"),
        (midx,        my,   mw/2, mh/2, PLOW,   "PLOWHORSE",
         "High demand\nLow margin", "Re-price /\ncut waste"),
    ]
    for x, y, w, h, col, name, desc, action in cells:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=col, alpha=0.14,
                     edgecolor=col, linewidth=1.3))
        ax.text(x + w/2, y + h*0.74, name, fontsize=11, fontweight="bold",
                color=col, ha="center", va="center")
        ax.text(x + w/2, y + h*0.46, desc, fontsize=7.8, color=INK,
                ha="center", va="center", linespacing=1.25)
        ax.text(x + w/2, y + h*0.18, action, fontsize=7.6, color=MUTED,
                ha="center", va="center", style="italic", linespacing=1.2)

    # axis arrows + average gridlines
    ax.annotate("", xy=(mx, my + mh + 0.025), xytext=(mx, my),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.3))
    ax.annotate("", xy=(mx + mw + 0.03, my), xytext=(mx, my),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.3))
    ax.text(mx - 0.018, midy, "Profitability  (profit per unit)  →",
            rotation=90, fontsize=8.6, color=INK, ha="center", va="center")
    ax.text(midx, my - 0.028, "Popularity  (units sold)  →",
            fontsize=8.6, color=INK, ha="center", va="center")
    ax.plot([mx, mx + mw], [midy, midy], color=FAINT, lw=0.9, ls=(0, (4, 3)))
    ax.plot([midx, midx], [my, my + mh], color=FAINT, lw=0.9, ls=(0, (4, 3)))
    ax.text(mx + mw + 0.012, midy, "avg\nprofit", fontsize=6.8, color=FAINT,
            va="center", linespacing=1.0)
    ax.text(midx, my + mh + 0.012, "avg popularity", fontsize=6.8, color=FAINT,
            ha="center")

    close(pdf, fig, ax, page_no)


# ----------------------------------------------------------------------------
# PAGE 6 — Worked example
# ----------------------------------------------------------------------------
def page_worked_example(pdf, page_no):
    fig, ax = new_page(pdf)
    c = Cursor(ax)

    c.h1("5.  A Worked Example")
    c.body(
        "To make the logic concrete, consider a small menu of four items over a "
        "reporting window. The table shows the aggregated sums the engine reads "
        "from the database, followed by the derived per-unit profit.")

    # data table
    data = [
        # name, Q, R, C(total), profit/unit, cat
        ("Margherita Pizza", 320, 224000, 89600,  STAR),
        ("Garlic Bread",     410, 102500, 73800,  PLOW),
        ("Truffle Risotto",   70,  98000,  42000, PUZZLE),
        ("House Salad",       90,  31500,  21600, DOG),
    ]
    headers = ["Item", "Q (units)", "R (Rs)", "C total (Rs)",
               "Profit/unit", "Class"]
    colx = [0.10, 0.34, 0.46, 0.585, 0.72, 0.84]
    y = c.y
    ax.add_patch(Rectangle((MARGIN_L, y - 0.024), MARGIN_R - MARGIN_L, 0.024,
                 color="#0f172a"))
    for hx, h in zip(colx, headers):
        ax.text(hx, y - 0.012, h, fontsize=8.0, color="white",
                va="center", fontweight="bold")
    y -= 0.024

    profits = []
    for i, (name, Q, R, C, col) in enumerate(data):
        prof = R / Q - C / Q
        profits.append(prof)
    avg_prof = sum(profits) / len(profits)
    avg_pop = sum(d[1] for d in data) / len(data)

    for i, (name, Q, R, C, col) in enumerate(data):
        prof = profits[i]
        bg = "#ffffff" if i % 2 else BOXBG
        ax.add_patch(Rectangle((MARGIN_L, y - 0.026), MARGIN_R - MARGIN_L, 0.026,
                     color=bg))
        vals = [name, f"{Q}", f"{R:,.0f}", f"{C:,.0f}", f"{prof:,.1f}"]
        for hx, v in zip(colx[:-1], vals):
            ax.text(hx, y - 0.013, v, fontsize=8.2, color=INK, va="center")
        # class chip
        cat_name = {STAR: "Star", PLOW: "Plow", PUZZLE: "Puzzle", DOG: "Dog"}[col]
        ax.add_patch(FancyBboxPatch((colx[5] - 0.004, y - 0.022), 0.072, 0.018,
                     boxstyle="round,pad=0.001,rounding_size=0.004",
                     linewidth=0, facecolor=col, alpha=0.9))
        ax.text(colx[5] + 0.032, y - 0.013, cat_name, fontsize=7.4,
                color="white", va="center", ha="center", fontweight="bold")
        y -= 0.026
    c.y = y - 0.016

    c.h2("Step-by-step for Margherita Pizza")
    c.body(
        f"Average unit price  = R / Q  = 224000 / 320  = Rs 700.0\n"
        f"Average unit cost   = C / Q  = 89600 / 320   = Rs 280.0\n"
        f"Profit per unit     = 700.0 − 280.0          = Rs 420.0")

    c.h2("Applying the thresholds")
    c.body(
        f"Average popularity across the four items = {avg_pop:,.0f} units.\n"
        f"Average profit per unit across the four items = Rs {avg_prof:,.1f}.")
    c.body(
        f"Margherita Pizza sells {data[0][1]} units (≥ {avg_pop:,.0f} → high "
        f"popularity) and earns Rs {profits[0]:,.0f}/unit "
        f"(≥ Rs {avg_prof:,.0f} → high profitability). Both axes high → it is a "
        f"STAR. Garlic Bread is popular but thin-margin → PLOWHORSE; Truffle "
        f"Risotto is rich-margin but slow → PUZZLE; House Salad is low on both "
        f"→ DOG.")

    close(pdf, fig, ax, page_no)


# ----------------------------------------------------------------------------
# PAGE 7 — Recommendations + insights
# ----------------------------------------------------------------------------
def page_recommendations(pdf, page_no):
    fig, ax = new_page(pdf)
    c = Cursor(ax)

    c.h1("6.  From Category to Action")
    c.body(
        "Classification is only useful if it produces a decision. The "
        "recommendation engine maps each category to a deterministic, "
        "rule-based action, a justification, a priority, and a confidence score. "
        "The mapping is fixed (not model-generated), which makes every "
        "suggestion auditable and reproducible.")

    cards = [
        (STAR, "Star", "High", "0.92",
         "Protect quality; feature in high-visibility menu positions.",
         "High demand and high per-unit profit."),
        (PLOW, "Plowhorse", "High", "0.88",
         "Test a small price increase, cut waste, or redesign portions.",
         "High demand but profit below the menu average."),
        (PUZZLE, "Puzzle", "Medium", "0.84",
         "Improve placement, naming, photography, staff prompts before discounting.",
         "Healthy profit but demand below average."),
        (DOG, "Dog", "Low", "0.82",
         "Remove, rework, or bundle unless it has strategic value.",
         "Low demand and low profit."),
    ]
    y = c.y
    for col, name, prio, conf, action, reason in cards:
        h = 0.085
        ax.add_patch(FancyBboxPatch((MARGIN_L, y - h), MARGIN_R - MARGIN_L, h - 0.008,
                     boxstyle="round,pad=0.003,rounding_size=0.006",
                     linewidth=1.0, edgecolor=col, facecolor=col, alpha=0.07))
        ax.add_patch(Rectangle((MARGIN_L, y - h), 0.010, h - 0.008, color=col))
        ax.text(MARGIN_L + 0.022, y - 0.016, name, fontsize=11,
                fontweight="bold", color=col, va="center")
        ax.text(MARGIN_R - 0.01, y - 0.016,
                f"priority {prio}   ·   confidence {conf}",
                fontsize=8.0, color=MUTED, va="center", ha="right")
        for j, line in enumerate(textwrap.wrap("Action:  " + action, width=96)):
            ax.text(MARGIN_L + 0.022, y - 0.034 - j * 0.0165, line,
                    fontsize=8.6, color=INK, va="center")
        ax.text(MARGIN_L + 0.022, y - 0.070, "Why:  " + reason,
                fontsize=8.4, color=MUTED, va="center", style="italic")
        y -= h + 0.006
    c.y = y - 0.006

    c.h1("7.  Business-Wide Insights")
    c.body(
        "Alongside per-item output, the engine summarizes the whole menu: total "
        "revenue, total units, and total gross profit (Σ GPᵢ); the revenue "
        "leader and the strongest profit contributor (max GPᵢ); a margin "
        "watchlist of the three lowest profit-per-unit items; the category mix "
        "counts; and a simple revenue trend.")
    c.formula(r"trend = up if $R_{\mathrm{last\,day}} > 1.1\,R_{\mathrm{first\,day}}$;  "
              r"down if $< 0.9\,R_{\mathrm{first\,day}}$;  else stable")

    close(pdf, fig, ax, page_no)


# ----------------------------------------------------------------------------
# PAGE 8 — Assumptions, limitations, conclusion
# ----------------------------------------------------------------------------
def page_limitations(pdf, page_no):
    fig, ax = new_page(pdf)
    c = Cursor(ax)

    c.h1("8.  Assumptions and Limitations")
    c.bullet("Relative, not absolute —", "categories are defined against the "
             "menu's own averages. Every item could be profitable in absolute "
             "terms and half will still be labelled 'low profit'. The matrix "
             "ranks within a menu; it does not certify viability.")
    c.bullet("Average-based thresholds —", "a single very-high-volume item drags "
             "the popularity average upward and can push moderate sellers below "
             "the line. Some practitioners prefer a 70%-of-average popularity "
             "rule or a median; this engine uses the plain mean for transparency.")
    c.bullet("Cost data quality —", "profit accuracy is bounded by COGS accuracy. "
             "With no cost column, unit_cost = 0 and 'profit' equals unit price. "
             "Fixed costs, labour, and wastage are out of scope — this is a "
             "contribution-margin model, not full cost accounting.")
    c.bullet("Per-unit averaging —", "price and cost are averaged over the window, "
             "so promotions, combos, and mid-period price changes are blended "
             "into a single effective margin per item.")
    c.bullet("Window sensitivity —", "thresholds are recomputed per query, so the "
             "same dish can change category as the date filter changes. This is "
             "intended (it reflects current performance) but means categories "
             "are not permanent labels.")

    c.gap(0.01)
    c.h1("9.  Conclusion")
    c.body(
        "MenuMind reduces an arbitrary sales export to four trustworthy numbers "
        "per dish, computes a per-unit contribution margin, and benchmarks every "
        "item against the menu's own popularity and profitability averages to "
        "assign one of four strategic categories. Each category carries a fixed, "
        "auditable recommendation. The pipeline is deliberately transparent: "
        "there is no black box between the raw upload and the Star/Plowhorse/"
        "Puzzle/Dog verdict — only the explicit arithmetic documented here.")

    c.gap(0.01)
    c.h2("Symbol reference")
    c.body(
        "Qᵢ — total units of item i      ·      Rᵢ — total revenue of item i\n"
        "Cᵢ — total cost (Σ unit_cost × q)      ·      p̄ᵢ — avg unit price = Rᵢ/Qᵢ\n"
        "c̄ᵢ — avg unit cost = Cᵢ/Qᵢ      ·      profitᵢ — per-unit profit = p̄ᵢ − c̄ᵢ\n"
        "GPᵢ — gross profit contribution = profitᵢ × Qᵢ\n"
        "Pop, Prof bars — menu-wide averages used as classification thresholds")

    close(pdf, fig, ax, page_no)


# ----------------------------------------------------------------------------
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "MenuMind_Methodology.pdf")
    with PdfPages(out) as pdf:
        page_title(pdf)
        page_overview(pdf, 2)
        page_ingestion(pdf, 3)
        page_profit(pdf, 4)
        page_classification(pdf, 5)
        page_worked_example(pdf, 6)
        page_recommendations(pdf, 7)
        page_limitations(pdf, 8)

        d = pdf.infodict()
        d["Title"] = "MenuMind — Menu-Engineering Methodology"
        d["Author"] = "MenuMind"
        d["Subject"] = "Profit calculation and item classification methodology"
        d["Keywords"] = "menu engineering, profit, Kasavana-Smith, Star Plowhorse Puzzle Dog"
    print("Wrote", out)


if __name__ == "__main__":
    main()
