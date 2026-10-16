# SAMPLE thumb-rule factors per sq ft of built-up area, and SAMPLE rates.
# These are rough, editable assumptions. They vary by region and design.
DEFAULT_FACTORS = {
    "Cement":           {"factor": 0.40, "unit": "bags (50 kg)", "rate": 400},
    "Sand":             {"factor": 1.20, "unit": "cu ft",        "rate": 60},
    "Coarse aggregate": {"factor": 1.35, "unit": "cu ft",        "rate": 55},
    "Steel":            {"factor": 4.00, "unit": "kg",           "rate": 65},
}


def estimate_materials(area, factor_rows, wall_length, wall_height,
                       wall_thk_in, opening_pct, bricks_per_cft, brick_rate):
    """Returns a list of rows: material, method, quantity, unit, rate, cost."""
    rows = []

    # Thumb-rule method: quantity = built-up area x factor
    for r in factor_rows:
        qty = area * r["Factor per sq ft"]
        rate = r["Rate (₹/unit)"]
        rows.append({
            "Material": r["Material"],
            "Method": f"{area:,.0f} sq ft × {r['Factor per sq ft']} per sq ft",
            "Quantity": qty, "Unit": r["Unit"],
            "Rate (₹)": rate, "Cost (₹)": qty * rate,
        })

    # Wall-volume method for bricks/blocks
    gross_vol = wall_length * wall_height * (wall_thk_in / 12)   # cu ft
    net_vol = gross_vol * (1 - opening_pct / 100)
    bricks = net_vol * bricks_per_cft
    rows.append({
        "Material": "Bricks / blocks",
        "Method": (f"{wall_length:,.0f} ft × {wall_height} ft × "
                   f"{wall_thk_in}/12 ft × (1 − {opening_pct}%) × "
                   f"{bricks_per_cft} per cu ft"),
        "Quantity": bricks, "Unit": "nos",
        "Rate (₹)": brick_rate, "Cost (₹)": bricks * brick_rate,
    })
    return rows