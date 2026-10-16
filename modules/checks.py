"""Parking fit check and room ventilation / daylight indicators.

Simple geometric and ratio checks only. Clearances and thresholds are values
the USER enters (the defaults are SAMPLE values, not building-code values).
Nothing here is a code-compliance check.
"""
import numpy as np
import pandas as pd

# Approximate SAMPLE vehicle sizes (length ft, width ft). Check your own vehicle's specifications.
VEHICLE_PRESETS = {
    "Small hatchback (sample size)": (11.5, 5.0),
    "Compact sedan / SUV (sample size)": (13.5, 5.8),
    "Large SUV / MUV (sample size)": (15.5, 6.2),
    "Two-wheeler (sample size)": (6.5, 2.5),
    "Custom (enter below)": None,
}

OPENING_LAYOUTS = {
    "None": ("No openings", 0),
    "One wall": ("Limited cross-ventilation (openings on one wall)", 1),
    "Two adjacent walls": ("Moderate cross-ventilation (adjacent walls)", 2),
    "Two opposite walls": ("Good cross-ventilation (opposite walls)", 3),
    "Three or more walls": ("Good cross-ventilation (three or more walls)", 3),
}

DEFAULT_ROOMS = [
    {"Room": "Living room", "Length (ft)": 15.0, "Width (ft)": 12.0, "Window area (sq ft)": 20.0,
     "Openable share (%)": 60.0, "Opening layout": "Two adjacent walls"},
    {"Room": "Kitchen", "Length (ft)": 10.0, "Width (ft)": 9.0, "Window area (sq ft)": 6.0,
     "Openable share (%)": 60.0, "Opening layout": "One wall"},
    {"Room": "Bedroom 1", "Length (ft)": 12.0, "Width (ft)": 11.0, "Window area (sq ft)": 9.0,
     "Openable share (%)": 50.0, "Opening layout": "One wall"},
    {"Room": "Bedroom 2", "Length (ft)": 12.0, "Width (ft)": 10.0, "Window area (sq ft)": 15.0,
     "Openable share (%)": 60.0, "Opening layout": "Two opposite walls"},
    {"Room": "Bathroom", "Length (ft)": 8.0, "Width (ft)": 5.0, "Window area (sq ft)": 0.0,
     "Openable share (%)": 50.0, "Opening layout": "None"},
]


# ---------------- Parking ----------------
def check_parking(space_l, space_w, veh_l, veh_w, n, end_clr, side_clr, tight):
    """Tests the proposed space against the vehicles for each arrangement and
    each way of turning the vehicles. All sizes in feet."""
    arrangements = [("Side by side", lambda: (veh_l + 2 * end_clr, n * veh_w + (n + 1) * side_clr))]
    if n > 1:
        arrangements.append(("One behind the other",
                             lambda: (n * veh_l + (n + 1) * end_clr, veh_w + 2 * side_clr)))
    options = []
    for name, need in arrangements:
        need_a, need_b = need()          # along the vehicle length, across the vehicles
        for rotated, (avail_a, avail_b) in (("Vehicle length along plot length", (space_l, space_w)),
                                            ("Vehicle length along plot width", (space_w, space_l))):
            m_a, m_b = avail_a - need_a, avail_b - need_b
            margin = min(m_a, m_b)
            status = "Does not fit" if margin < -1e-9 else ("Fits, but tight" if margin < tight else "Fits")
            options.append({"Arrangement": name, "Orientation": rotated,
                            "Needed (ft)": f"{need_a:.1f} × {need_b:.1f}",
                            "Available (ft)": f"{avail_a:.1f} × {avail_b:.1f}",
                            "Spare length (ft)": round(m_a, 2), "Spare width (ft)": round(m_b, 2),
                            "Margin": round(margin, 2), "Status": status,
                            "_need": (need_a, need_b), "_avail": (avail_a, avail_b),
                            "_rot": rotated.endswith("width"), "_arr": name})
    options.sort(key=lambda o: -o["Margin"])
    return options


def parking_rects(opt, veh_l, veh_w, n):
    """Vehicle rectangles (x0, y0, dx, dy) with x = plot width, y = plot length."""
    avail_a, avail_b = opt["_avail"]
    rects = []
    if opt["_arr"] == "Side by side":
        gap = (avail_b - n * veh_w) / (n + 1)
        a0 = (avail_a - veh_l) / 2
        for i in range(n):
            rects.append((a0, gap + i * (veh_w + gap), veh_l, veh_w))      # (a0, b0, size_a, size_b)
    else:
        gap = (avail_a - n * veh_l) / (n + 1)
        b0 = (avail_b - veh_w) / 2
        for i in range(n):
            rects.append((gap + i * (veh_l + gap), b0, veh_l, veh_w))
    out = []
    for a0, b0, sa, sb in rects:
        if opt["_rot"]:
            out.append((a0, b0, sa, sb))      # a -> plot width (x), b -> plot length (y)
        else:
            out.append((b0, a0, sb, sa))      # a -> plot length (y), b -> plot width (x)
    return out


# ---------------- Ventilation and daylight ----------------
def check_rooms(df, min_daylight, min_vent):
    """Adds indicator columns to the room table. Returns (table, findings)."""
    t = df.copy()
    for c in ["Length (ft)", "Width (ft)", "Window area (sq ft)", "Openable share (%)"]:
        t[c] = pd.to_numeric(t[c], errors="coerce")
    t["Room"] = t["Room"].fillna("").astype(str).str.strip()
    t = t[(t["Room"] != "") | t[["Length (ft)", "Width (ft)"]].notna().any(axis=1)].reset_index(drop=True)
    t["Floor area (sq ft)"] = t["Length (ft)"] * t["Width (ft)"]
    t["Window-to-floor (%)"] = t["Window area (sq ft)"] / t["Floor area (sq ft)"] * 100
    t["Openable area (sq ft)"] = t["Window area (sq ft)"] * t["Openable share (%)"] / 100
    t["Openable-to-floor (%)"] = t["Openable area (sq ft)"] / t["Floor area (sq ft)"] * 100

    findings, daylight, vent, cross, overall = [], [], [], [], []
    for _, r in t.iterrows():
        name = r["Room"] or "(unnamed room)"
        area, win, opn = r["Floor area (sq ft)"], r["Window area (sq ft)"], r["Openable area (sq ft)"]
        layout = r["Opening layout"] if r["Opening layout"] in OPENING_LAYOUTS else "None"
        cross_text, cross_score = OPENING_LAYOUTS[layout]
        problems = []
        if win <= 0:
            d_status = v_status = "No openings"
            problems.append(f"{name}: no window or opening was entered. Natural light and ventilation "
                            f"would depend on other means, which need professional review.")
        else:
            d_ok = r["Window-to-floor (%)"] >= min_daylight
            v_ok = r["Openable-to-floor (%)"] >= min_vent
            d_status = "Meets your threshold" if d_ok else "Below your threshold"
            v_status = "Meets your threshold" if v_ok else "Below your threshold"
            if not d_ok or not v_ok:
                need_win = max(min_daylight / 100 * area - win,
                               (min_vent / 100 * area - opn) / (r["Openable share (%)"] / 100)
                               if r["Openable share (%)"] > 0 else np.inf)
                extra = "" if np.isinf(need_win) else f" Roughly {max(need_win, 0):.1f} sq ft more window area would reach both thresholds."
                bits = []
                if not d_ok:
                    bits.append(f"window-to-floor ratio is {r['Window-to-floor (%)']:.1f}% (threshold {min_daylight:g}%)")
                if not v_ok:
                    bits.append(f"openable-to-floor ratio is {r['Openable-to-floor (%)']:.1f}% (threshold {min_vent:g}%)")
                problems.append(f"{name}: " + " and ".join(bits) + "." + extra)
        if cross_score == 1 and win > 0:
            problems.append(f"{name}: openings on only one wall give limited cross-ventilation. "
                            f"Consider an opening on a second wall if the layout allows.")
        findings += problems
        daylight.append(d_status)
        vent.append(v_status)
        cross.append(cross_text)
        overall.append("Review" if problems else "OK")
    t["Daylight indicator"] = daylight
    t["Ventilation indicator"] = vent
    t["Cross-ventilation indicator"] = cross
    t["Result"] = overall
    return t, findings