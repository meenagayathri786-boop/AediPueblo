import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modules.checks import (DEFAULT_ROOMS, OPENING_LAYOUTS, VEHICLE_PRESETS,
                            check_parking, check_rooms, parking_rects)

st.title("Parking and Ventilation Assessment")
st.warning("SIMPLE INDICATORS ONLY. Clearances and thresholds below are SAMPLE values that YOU "
           "should replace with your own needs and your local rules. This page does not check "
           "building-code compliance. Items marked 'Review' need a qualified professional.")

layout = st.session_state.get("layout_result")
tab_p, tab_v = st.tabs(["Parking", "Ventilation and daylight"])

# =============================== PARKING ======================================
with tab_p:
    st.subheader("Parking space and vehicle")
    park_room = next((r for r in layout["rooms"] if r["type"] == "Parking"), None) if layout else None
    if park_room:
        d_l, d_w = round(park_room["dy"], 1), round(park_room["dx"], 1)
        st.caption(f"Default space taken from the top-ranked layout ({layout['name']}): "
                   f"{d_w:g} ft wide × {d_l:g} ft long.")
    else:
        d_l, d_w = 18.0, 9.0
        st.caption("Tip: open Layout Comparison first to take the parking size from the top layout.")

    a1, a2, a3 = st.columns(3)
    space_l = a1.number_input("Proposed parking length (ft)", min_value=0.0, value=float(d_l), step=0.5)
    space_w = a2.number_input("Proposed parking width (ft)", min_value=0.0, value=float(d_w), step=0.5)
    n = a3.number_input("Number of vehicles", min_value=1, max_value=4, value=1, step=1)

    preset = st.selectbox("Vehicle type", list(VEHICLE_PRESETS), index=0)
    sample = VEHICLE_PRESETS[preset] or (11.5, 5.0)
    b1, b2 = st.columns(2)
    veh_l = b1.number_input("Vehicle length (ft)", min_value=1.0, value=float(sample[0]), step=0.1,
                            key=f"vl_{preset}", help="Approximate sample size. Use your vehicle's real size.")
    veh_w = b2.number_input("Vehicle width (ft)", min_value=1.0, value=float(sample[1]), step=0.1,
                            key=f"vw_{preset}", help="Body width without mirrors. Use your vehicle's real size.")

    c1, c2, c3, c4 = st.columns(4)
    end_clr = c1.number_input("Clearance at each end (ft)", min_value=0.0, value=1.5, step=0.5,
                              help="Space in front of and behind each vehicle. Sample value, your choice.")
    side_clr = c2.number_input("Clearance at each side (ft)", min_value=0.0, value=1.5, step=0.5,
                               help="Space beside each vehicle for opening doors. Sample value, your choice.")
    tight = c3.number_input("'Tight' if spare space is below (ft)", min_value=0.0, value=1.0, step=0.5)
    gate_w = c4.number_input("Entry / gate width (ft), optional", min_value=0.0, value=0.0, step=0.5,
                             help="Leave at 0 to skip the entry check.")

    if space_l <= 0 or space_w <= 0:
        st.error("Parking length and width must be greater than zero.")
    else:
        opts = check_parking(space_l, space_w, veh_l, veh_w, int(n), end_clr, side_clr, tight)
        best = opts[0]
        if best["Status"] == "Fits":
            st.success(f"The vehicle(s) fit: {best['Arrangement'].lower()}, {best['Orientation'].lower()}. "
                       f"Smallest spare space: {best['Margin']:.1f} ft.")
        elif best["Status"] == "Fits, but tight":
            st.warning(f"The vehicle(s) fit but only just ({best['Arrangement'].lower()}, "
                       f"{best['Orientation'].lower()}). Smallest spare space: {best['Margin']:.1f} ft. "
                       f"Moving in and out may be difficult. Flagged for professional review.")
        else:
            st.error(f"The vehicle(s) do not fit with the clearances entered. The best option is short by "
                     f"{abs(best['Margin']):.1f} ft in one direction ({best['Arrangement'].lower()}, "
                     f"{best['Orientation'].lower()}). Increase the space, reduce the clearances, or "
                     f"use fewer or smaller vehicles.")

        if gate_w > 0:
            need_gate = veh_w + 2 * 1.0
            if gate_w + 1e-9 >= need_gate:
                st.info(f"Entry width {gate_w:g} ft is at least vehicle width + 1 ft each side ({need_gate:g} ft).")
            else:
                st.warning(f"Entry width {gate_w:g} ft is less than vehicle width + 1 ft each side "
                           f"({need_gate:g} ft). Review the gate or entry width.")

        st.markdown("**All options tested**")
        st.table(pd.DataFrame(opts)[["Arrangement", "Orientation", "Needed (ft)", "Available (ft)",
                                     "Spare length (ft)", "Spare width (ft)", "Status"]])

        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=space_w, y1=space_l, fillcolor="#eeeeee",
                      line=dict(color="black", width=2))
        for x, y, dx, dy in parking_rects(best, veh_l, veh_w, int(n)):
            fig.add_shape(type="rect", x0=x, y0=y, x1=x + dx, y1=y + dy, fillcolor="#90caf9",
                          line=dict(color="#1565c0"))
            fig.add_annotation(x=x + dx / 2, y=y + dy / 2, text=f"Vehicle<br>{veh_l:g} × {veh_w:g} ft",
                               showarrow=False, font=dict(size=10, color="black"))
        fig.update_xaxes(range=[-1, space_w + 1], title="Width (ft)")
        fig.update_yaxes(range=[-1, space_l + 1], title="Length (ft)", scaleanchor="x", scaleratio=1)
        fig.update_layout(title="Best option drawn to scale (grey = proposed parking space)", height=480)
        st.plotly_chart(fig, width="stretch")

        parking_result = {"status": best["Status"], "margin": best["Margin"], "vehicles": int(n),
                          "option": f"{best['Arrangement']}, {best['Orientation']}",
                          "space": f"{space_w:g} × {space_l:g} ft", "vehicle": f"{veh_l:g} × {veh_w:g} ft"}
        st.session_state["parking_result"] = parking_result

# ======================== VENTILATION AND DAYLIGHT ============================
with tab_v:
    st.subheader("Room openings")
    st.caption("Enter the rooms and their window areas. The values in the table are PLACEHOLDERS: "
               "replace them with your planned room sizes and openings.")
    if layout:
        rows = []
        for r in layout["rooms"]:
            if r["type"] == "Parking":
                continue
            rows.append({"Room": r["name"], "Length (ft)": round(max(r["dx"], r["dy"]), 1),
                         "Width (ft)": round(min(r["dx"], r["dy"]), 1),
                         "Window area (sq ft)": 3.0 if r["type"] == "Bathroom" else 12.0,
                         "Openable share (%)": 50.0, "Opening layout": "One wall"})
        base = pd.DataFrame(rows)
        key = "v_" + layout["name"]
        st.caption(f"Room sizes taken from the top-ranked layout ({layout['name']}). "
                   f"Window values are placeholders.")
    else:
        base, key = pd.DataFrame(DEFAULT_ROOMS), "v_sample"
        st.caption("Showing a SAMPLE room list. Open Layout Comparison first to use your own layout's rooms.")

    t1, t2 = st.columns(2)
    min_day = t1.number_input("Daylight threshold: window area as % of floor area", min_value=0.0,
                              value=10.0, step=1.0,
                              help="SAMPLE value, not a code requirement. Use the figure from your local rules or your designer.")
    min_vent = t2.number_input("Ventilation threshold: openable area as % of floor area", min_value=0.0,
                               value=5.0, step=0.5,
                               help="SAMPLE value, not a code requirement. Use the figure from your local rules or your designer.")

    edited = st.data_editor(
        base, num_rows="dynamic", hide_index=True, key=key,
        column_config={
            "Opening layout": st.column_config.SelectboxColumn(options=list(OPENING_LAYOUTS)),
            "Openable share (%)": st.column_config.NumberColumn(min_value=0.0, max_value=100.0),
            "Length (ft)": st.column_config.NumberColumn(min_value=0.0),
            "Width (ft)": st.column_config.NumberColumn(min_value=0.0),
            "Window area (sq ft)": st.column_config.NumberColumn(min_value=0.0),
        })

    table, findings = check_rooms(edited, min_day, min_vent)
    bad = table[(table["Length (ft)"].isna()) | (table["Width (ft)"].isna())
                | (table["Length (ft)"] <= 0) | (table["Width (ft)"] <= 0)
                | table["Window area (sq ft)"].isna() | table["Openable share (%)"].isna()]
    if table.empty:
        st.warning("Enter at least one room.")
    elif not bad.empty:
        st.error("Every room needs a length, width, window area and openable share (length and width above zero). "
                 "Please complete the table.")
    else:
        if (table["Window area (sq ft)"] > table["Floor area (sq ft)"]).any():
            st.warning("A window area is larger than its room's floor area. Please check the numbers.")
        show = table[["Room", "Floor area (sq ft)", "Window-to-floor (%)", "Openable-to-floor (%)",
                      "Daylight indicator", "Ventilation indicator", "Cross-ventilation indicator",
                      "Result"]].round(1)
        st.markdown("**Results**")
        st.dataframe(show, hide_index=True, width="stretch")

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Window-to-floor (%)", x=table["Room"], y=table["Window-to-floor (%)"],
                             marker_color="#fbc02d"))
        fig.add_trace(go.Bar(name="Openable-to-floor (%)", x=table["Room"], y=table["Openable-to-floor (%)"],
                             marker_color="#1565c0"))
        fig.add_hline(y=min_day, line_dash="dash", line_color="#f9a825",
                      annotation_text=f"Daylight threshold {min_day:g}%")
        fig.add_hline(y=min_vent, line_dash="dash", line_color="#1565c0",
                      annotation_text=f"Ventilation threshold {min_vent:g}%")
        fig.update_layout(barmode="group", title="Opening ratios by room vs your thresholds",
                          yaxis_title="% of floor area")
        st.plotly_chart(fig, width="stretch")

        st.markdown("**Findings (rule-based, not AI)**")
        if findings:
            for f in findings:
                st.markdown("- " + f)
        else:
            st.success("All rooms meet the thresholds you entered. This is an indicator only.")

        st.session_state["ventilation_result"] = {
            "rooms_checked": int(len(table)), "rooms_review": int((table["Result"] == "Review").sum()),
            "findings": findings, "min_daylight": min_day, "min_vent": min_vent}

# ============================ LIMITATIONS =====================================
with st.expander("Formulas, assumptions and limitations"):
    st.markdown("""
**Parking.** Needed size, one vehicle or side by side = (vehicle length + 2 × end clearance) by
(number × vehicle width + (number + 1) × side clearance). One behind the other = (number × vehicle length +
(number + 1) × end clearance) by (vehicle width + 2 × side clearance). Spare space = available − needed.
The check is repeated with the vehicles turned 90° and the best option is shown.

**Ventilation and daylight.** Window-to-floor % = window area ÷ floor area × 100. Openable-to-floor % =
window area × openable share ÷ floor area × 100. Both are compared with the thresholds YOU enter.
Cross-ventilation is judged only from which walls have openings, as you enter them.

**Not assessed.** Turning space and driveway geometry, ramp slopes, headroom, gate swing, fire safety, structure,
sun direction and shading, window height, obstructions outside, mechanical ventilation, and any local
building rules. Rooms marked 'Review' and tight parking should be checked by an architect or engineer.
""")