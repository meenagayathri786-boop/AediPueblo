"""Contractor quotation checker.

Rule-based checks only (no AI model, no machine learning). Every flag is a
QUESTION to ask the contractor, not an accusation. A flag can have an innocent
explanation (different scope, brand, quality, wastage, a typing slip).
"""
import re
from difflib import SequenceMatcher

import numpy as np
import pandas as pd

COLUMNS = ["Item", "Unit", "Quantity", "Rate (₹)", "Amount (₹)",
           "Reference rate (₹)", "Expected qty"]
NUMERIC = ["Quantity", "Rate (₹)", "Amount (₹)", "Reference rate (₹)", "Expected qty"]

# SAMPLE quotation with a few deliberate issues so the checker can be demonstrated.
# All numbers are made up for demonstration. Replace them with real quotation data.
SAMPLE_QUOTATION = [
    {"Item": "Cement (OPC 53)", "Unit": "bag", "Quantity": 600, "Rate (₹)": 420,
     "Amount (₹)": 252000, "Reference rate (₹)": 400, "Expected qty": 576},
    {"Item": "River sand", "Unit": "cu ft", "Quantity": 2200, "Rate (₹)": 62,
     "Amount (₹)": 136400, "Reference rate (₹)": 60, "Expected qty": 1728},
    {"Item": "Coarse aggregate 20 mm", "Unit": "cu ft", "Quantity": 1950, "Rate (₹)": 55,
     "Amount (₹)": 107250, "Reference rate (₹)": 55, "Expected qty": 1944},
    {"Item": "TMT steel bars", "Unit": "kg", "Quantity": 5800, "Rate (₹)": 90,
     "Amount (₹)": 522000, "Reference rate (₹)": 65, "Expected qty": 5760},
    {"Item": "Bricks", "Unit": "nos", "Quantity": 26800, "Rate (₹)": 8,
     "Amount (₹)": 214400, "Reference rate (₹)": 8, "Expected qty": 26775},
    {"Item": "Plastering", "Unit": "sq ft", "Quantity": 3000, "Rate (₹)": 38,
     "Amount (₹)": 114000, "Reference rate (₹)": 35, "Expected qty": np.nan},
    {"Item": "Flooring tiles", "Unit": "sq ft", "Quantity": 1400, "Rate (₹)": 95,
     "Amount (₹)": 133000, "Reference rate (₹)": 90, "Expected qty": np.nan},
    {"Item": "Doors and windows", "Unit": "nos", "Quantity": 8, "Rate (₹)": 11500,
     "Amount (₹)": 98000, "Reference rate (₹)": np.nan, "Expected qty": np.nan},
    {"Item": "Electrical work", "Unit": "lump sum", "Quantity": 1, "Rate (₹)": 120000,
     "Amount (₹)": 120000, "Reference rate (₹)": np.nan, "Expected qty": np.nan},
    {"Item": "Cement OPC 53", "Unit": "bag", "Quantity": 60, "Rate (₹)": 420,
     "Amount (₹)": 25200, "Reference rate (₹)": 400, "Expected qty": np.nan},
    {"Item": "Waterproofing", "Unit": "sq ft", "Quantity": np.nan, "Rate (₹)": 22,
     "Amount (₹)": 30800, "Reference rate (₹)": np.nan, "Expected qty": np.nan},
]
SAMPLE_STATED_TOTAL = 1730000.0

PRIORITY_ORDER = {"Check first": 0, "Review": 1, "Note": 2}


def _num(x):
    if x is None:
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = re.sub(r"[₹,\s]|rs\.?|inr", "", str(x), flags=re.I)
    try:
        return float(s)
    except ValueError:
        return np.nan


def _norm(name):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(name).lower())).strip()


def map_columns(raw):
    """Maps the column names of an uploaded file onto the standard columns.
    Returns (table, problems)."""
    taken, mapping = set(), {}

    def pick(target, test):
        for c in raw.columns:
            if c in taken:
                continue
            if test(str(c).lower()):
                mapping[target] = c
                taken.add(c)
                return

    pick("Reference rate (₹)", lambda n: "ref" in n)
    pick("Expected qty", lambda n: "expect" in n)
    pick("Amount (₹)", lambda n: any(k in n for k in ("amount", "total", "value", "cost")))
    pick("Rate (₹)", lambda n: "rate" in n or "price" in n)
    pick("Quantity", lambda n: "qty" in n or "quantity" in n)
    pick("Unit", lambda n: n.strip() in ("unit", "uom", "units") or n.startswith("unit"))
    pick("Item", lambda n: any(k in n for k in ("item", "descr", "particular", "work", "material")))

    problems = [f"Could not find a column for '{t}'." for t in ("Item", "Quantity", "Rate (₹)")
                if t not in mapping]
    out = pd.DataFrame({c: raw[mapping[c]] if c in mapping else np.nan for c in COLUMNS},
                       index=raw.index)
    return out, problems


def check_quotation(df, stated_total=0.0, rate_tol=20.0, qty_tol=15.0, abs_tol=1.0):
    """Returns (items_df, flags_df, summary_dict)."""
    d = df.copy()
    for c in COLUMNS:
        if c not in d.columns:
            d[c] = np.nan
    for c in NUMERIC:
        d[c] = d[c].map(_num)
    d["Item"] = d["Item"].fillna("").astype(str).str.strip()
    d["Unit"] = d["Unit"].fillna("").astype(str).str.strip()
    d["Row"] = np.arange(1, len(d) + 1)
    used = (d["Item"] != "") | d[["Quantity", "Rate (₹)", "Amount (₹)"]].notna().any(axis=1)
    d = d[used].reset_index(drop=True)

    has_amount = d["Amount (₹)"].notna().any()
    d["Calc amount (₹)"] = d["Quantity"] * d["Rate (₹)"]
    d["Amount diff (₹)"] = d["Amount (₹)"] - d["Calc amount (₹)"]
    d["Rate vs ref (%)"] = np.where(d["Reference rate (₹)"] > 0,
                                    (d["Rate (₹)"] - d["Reference rate (₹)"]) / d["Reference rate (₹)"] * 100,
                                    np.nan)
    d["Qty vs expected (%)"] = np.where(d["Expected qty"] > 0,
                                        (d["Quantity"] - d["Expected qty"]) / d["Expected qty"] * 100,
                                        np.nan)

    flags = []

    def add(row, item, prio, check, finding, ask):
        flags.append({"Row": row, "Item": item or "(no description)", "Priority": prio,
                      "Check": check, "Finding": finding, "Suggested question": ask})

    for _, r in d.iterrows():
        row, item = int(r["Row"]), r["Item"]
        q, rt, am = r["Quantity"], r["Rate (₹)"], r["Amount (₹)"]

        if item == "":
            add(row, item, "Check first", "Missing entry", "The item description is empty.",
                "Ask what work or material this line covers.")
        if np.isnan(q) or q == 0:
            add(row, item, "Check first", "Missing entry", "Quantity is missing or zero.",
                "Ask for the quantity and how it was measured.")
        elif q < 0:
            add(row, item, "Check first", "Inconsistent quantity", f"Quantity is negative ({q:g}).",
                "Ask whether this is a credit/deduction or a typing error.")
        if np.isnan(rt) or rt == 0:
            add(row, item, "Check first", "Missing entry", "Rate is missing or zero.",
                "Ask for the rate, or whether this item is included elsewhere.")
        elif rt < 0:
            add(row, item, "Check first", "Inconsistent rate", f"Rate is negative ({rt:g}).",
                "Ask whether this is a deduction or a typing error.")
        if has_amount and np.isnan(am):
            add(row, item, "Note", "Missing entry", "Amount is missing.",
                "Ask for the line amount.")
        if item != "" and r["Unit"] == "":
            add(row, item, "Note", "Missing entry", "Unit is missing.",
                "Ask which unit the quantity and rate refer to.")

        if not (np.isnan(q) or np.isnan(rt) or np.isnan(am)):
            diff = am - q * rt
            if abs(diff) > abs_tol:
                word = "higher" if diff > 0 else "lower"
                add(row, item, "Check first", "Arithmetic",
                    f"Quoted amount ₹{am:,.0f} is ₹{abs(diff):,.0f} {word} than "
                    f"quantity × rate = {q:g} × {rt:g} = ₹{q * rt:,.0f}.",
                    "Ask which of quantity, rate or amount is correct.")

        dev = r["Rate vs ref (%)"]
        if not np.isnan(dev) and abs(dev) > rate_tol:
            prio = "Check first" if abs(dev) > 2 * rate_tol else "Review"
            if dev > 0:
                txt = (f"Rate ₹{rt:g} is {dev:.0f}% above your reference rate ₹{r['Reference rate (₹)']:g}.")
                ask = "Ask what grade, brand, delivery or scope the rate covers."
            else:
                txt = (f"Rate ₹{rt:g} is {abs(dev):.0f}% below your reference rate ₹{r['Reference rate (₹)']:g}.")
                ask = "Ask whether quality, scope or quantity differs from what you expect."
            add(row, item, prio, "Rate vs reference", txt, ask)

        qd = r["Qty vs expected (%)"]
        if not np.isnan(qd) and abs(qd) > qty_tol:
            add(row, item, "Review", "Inconsistent quantity",
                f"Quantity {q:g} is {abs(qd):.0f}% {'above' if qd > 0 else 'below'} your expected "
                f"quantity {r['Expected qty']:g}.",
                "Ask how the contractor measured the quantity, and what wastage is allowed.")

    # Duplicates
    groups = {}
    for _, r in d.iterrows():
        k = _norm(r["Item"])
        if k:
            groups.setdefault(k, []).append(r)
    for k, rows in groups.items():
        if len(rows) > 1:
            nums = ", ".join(str(int(x["Row"])) for x in rows)
            tot_q = np.nansum([x["Quantity"] for x in rows])
            add(int(rows[0]["Row"]), rows[0]["Item"], "Review", "Possible duplicate",
                f"This item appears {len(rows)} times (rows {nums}). Combined quantity: "
                f"{tot_q:g} {rows[0]['Unit']}.",
                "Ask whether these are separate works or the same item entered twice.")
    keys = list(groups)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if SequenceMatcher(None, keys[i], keys[j]).ratio() >= 0.88:
                a, b = groups[keys[i]][0], groups[keys[j]][0]
                add(int(a["Row"]), a["Item"], "Note", "Possible duplicate",
                    f"Description is very similar to row {int(b['Row'])} ('{b['Item']}').",
                    "Ask whether these two lines overlap.")

    # Totals
    quoted_total = float(np.nansum(d["Amount (₹)"])) if has_amount else np.nan
    calc_total = float(np.nansum(d["Calc amount (₹)"]))
    if has_amount and abs(quoted_total - calc_total) > abs_tol:
        add("-", "(whole quotation)", "Review", "Arithmetic",
            f"Sum of quoted line amounts ₹{quoted_total:,.0f} differs from the sum of "
            f"quantity × rate ₹{calc_total:,.0f} by ₹{abs(quoted_total - calc_total):,.0f}.",
            "Ask for a corrected line-by-line breakdown.")
    if stated_total and stated_total > 0:
        base = quoted_total if has_amount else calc_total
        if abs(stated_total - base) > abs_tol:
            word = "higher" if stated_total > base else "lower"
            add("-", "(whole quotation)", "Check first", "Arithmetic",
                f"The total stated on the quotation (₹{stated_total:,.0f}) is ₹{abs(stated_total - base):,.0f} "
                f"{word} than the sum of the line amounts (₹{base:,.0f}).",
                "Ask how the stated total was calculated (taxes, discounts, or items not listed?).")

    has_ref = d["Reference rate (₹)"] > 0
    ref_part = d[has_ref & d["Quantity"].notna() & d["Rate (₹)"].notna()]
    summary = {
        "n_items": int(len(d)),
        "quoted_total": quoted_total,
        "calc_total": calc_total,
        "stated_total": float(stated_total) if stated_total else np.nan,
        "ref_items": int(len(ref_part)),
        "ref_quoted": float((ref_part["Quantity"] * ref_part["Rate (₹)"]).sum()),
        "ref_at_ref": float((ref_part["Quantity"] * ref_part["Reference rate (₹)"]).sum()),
    }
    flags_df = pd.DataFrame(flags, columns=["Row", "Item", "Priority", "Check",
                                            "Finding", "Suggested question"])
    if not flags_df.empty:
        flags_df["_o"] = flags_df["Priority"].map(PRIORITY_ORDER)
        flags_df = flags_df.sort_values(["_o"], kind="stable").drop(columns="_o").reset_index(drop=True)
    return d, flags_df, summary