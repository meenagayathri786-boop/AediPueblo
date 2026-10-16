import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.materials import DEFAULT_FACTORS, estimate_materials

st.title("Material Quantity Estimator")
st.warning("PRELIMINARY ESTIMATE ONLY. Factors and rates are SAMPLE values. "
           "This is not a detailed engineering quantity take-off or bill of quantities.")

cost = st.session_state.get("cost_result")
default_area = float(cost["total_area"]) if cost else 1000.0
if cost:
    st.caption(f"Default area taken from the Cost Estimator: {default_area:,.0f} sq ft.")

area = st.number_input("Total built-up area (sq ft)", min_value=0.0,
                       value=default_area, step=50.0)

st.subheader("1. Thumb-rule materials (editable)")
df = pd.DataFrame([
    {"Material": k, "Factor per sq ft": v["factor"],
     "Unit": v["unit"], "Rate (₹/unit)": v["rate"]}
    for k, v in DEFAULT_FACTORS.items()
])
edited = st.data_editor(df, disabled=["Material", "Unit"], hide_index=True)

st.subheader("2. Bricks / blocks (wall volume method)")
c1, c2, c3 = st.columns(3)
with c1:
    wall_length = st.number_input("Total wall length (ft)", min_value=0.0,
                                  value=300.0, step=10.0,
                                  help="Sum of all external and internal walls. Sample value.")
    wall_height = st.number_input("Wall height (ft)", min_value=0.0, value=10.0, step=0.5)
with c2:
    wall_thk = st.number_input("Wall thickness (inches)", min_value=0.0, value=9.0, step=1.0)
    opening = st.number_input("Openings deducted (%)", min_value=0.0,
                              max_value=90.0, value=15.0, step=1.0,
                              help="Doors and windows. Sample value.")
with c3:
    bricks_per_cft = st.number_input("Bricks per cu ft of wall", min_value=0.0,
                                     value=14.0, step=0.5,
                                     help="About 500 per cubic metre including mortar. Sample value.")
    brick_rate = st.number_input("Brick rate (₹ each)", min_value=0.0, value=8.0, step=0.5)

# Validation
if area <= 0:
    st.error("Built-up area must be greater than zero.")
    st.stop()
if (edited["Factor per sq ft"] < 0).any() or (edited["Rate (₹/unit)"] < 0).any():
    st.error("Factors and rates cannot be negative.")
    st.stop()

rows = estimate_materials(area, edited.to_dict("records"), wall_length,
                          wall_height, wall_thk, opening, bricks_per_cft, brick_rate)
res = pd.DataFrame(rows)
total = res["Cost (₹)"].sum()
st.session_state["material_result"] = {"rows": rows, "total": total}

st.subheader("Results")
show = res.copy()
show["Quantity"] = show["Quantity"].map("{:,.0f}".format)
show["Rate (₹)"] = show["Rate (₹)"].map("{:,.1f}".format)
show["Cost (₹)"] = show["Cost (₹)"].map("{:,.0f}".format)
st.table(show[["Material", "Method", "Quantity", "Unit", "Rate (₹)", "Cost (₹)"]])

m1, m2 = st.columns(2)
m1.metric("Estimated material cost", f"₹ {total:,.0f}")
if cost:
    share = total / cost["total_cost"] * 100
    m2.metric("Share of total construction estimate", f"{share:.1f}%")

fig = go.Figure(go.Bar(x=res["Material"], y=res["Cost (₹)"], marker_color="#2e7d32"))
fig.update_layout(title="Estimated cost by material", yaxis_title="₹")
st.plotly_chart(fig, width="stretch")

with st.expander("Formulas and assumptions"):
    st.markdown("""
- Cement, sand, aggregate, steel: quantity = built-up area × factor per sq ft
- Bricks: wall length × height × (thickness ÷ 12) × (1 − openings %) × bricks per cu ft
- Cost = quantity × rate
- All factors and rates are sample, editable values. Real quantities depend on structural
  design, wastage, and site conditions.
- Material cost here is not the same as the total construction cost, which also includes labour and other items.
- A qualified engineer must prepare detailed quantities before any purchase or tendering.
    """)