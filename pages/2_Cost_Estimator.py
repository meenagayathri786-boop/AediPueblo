import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.cost import DEFAULT_CATEGORIES, estimate_cost

st.title("Cost Estimator")
st.info("Rates and percentages below are SAMPLE values. "
        "Change them to match your local conditions.")

# Use buildable area from the Plot Analysis page if available
plot = st.session_state.get("plot_result")
default_area = float(plot["buildable_area"]) if plot else 1000.0
if plot:
    st.caption(f"Default area taken from Plot Analysis: "
               f"{default_area:,.0f} sq ft (maximum footprint). "
               f"Reduce it if you plan to build on less.")
else:
    st.caption("Tip: open the Plot Analysis page first to fill the area automatically.")

c1, c2 = st.columns(2)
with c1:
    area = st.number_input("Built-up area per floor (sq ft)", min_value=0.0,
                           value=default_area, step=50.0)
    floors = st.number_input("Number of floors", min_value=1, value=1, step=1)
with c2:
    rate = st.number_input("Construction cost per sq ft (₹)", min_value=0.0,
                           value=1800.0, step=50.0,
                           help="Sample value. Use a local rate.")
    budget = st.number_input("Available budget (₹)", min_value=0.0,
                             value=2500000.0, step=50000.0)

st.subheader("Cost categories (editable)")
share_df = pd.DataFrame({
    "Category": list(DEFAULT_CATEGORIES.keys()),
    "Share (%)": list(DEFAULT_CATEGORIES.values()),
})
edited = st.data_editor(share_df, disabled=["Category"], hide_index=True,
                        use_container_width=False)

# Validation
total_share = edited["Share (%)"].sum()
if area <= 0 or rate <= 0:
    st.error("Area and cost per sq ft must be greater than zero.")
    st.stop()
if abs(total_share - 100) > 0.01:
    st.error(f"Category shares add up to {total_share:.1f}%. They must total 100%.")
    st.stop()

shares = dict(zip(edited["Category"], edited["Share (%)"]))
res = estimate_cost(area, floors, rate, shares)
total = res["total_cost"]
st.session_state["cost_result"] = res
st.session_state["cost_inputs"] = {"budget": budget, "rate": rate, "floors": floors}

# Budget comparison
st.subheader("Estimate vs budget")
diff = budget - total
m1, m2, m3 = st.columns(3)
m1.metric("Total built-up area", f"{res['total_area']:,.0f} sq ft")
m2.metric("Estimated cost", f"₹ {total:,.0f}")
m3.metric("Budget difference", f"₹ {diff:,.0f}",
          delta="within budget" if diff >= 0 else "over budget",
          delta_color="normal" if diff >= 0 else "inverse")

if diff >= 0:
    st.success(f"The estimate is ₹ {diff:,.0f} below your budget.")
else:
    st.error(f"The estimate exceeds your budget by ₹ {-diff:,.0f} "
             f"({-diff / budget * 100:.1f}% over).")

# Breakdown table
st.subheader("Cost breakdown")
table = pd.DataFrame({
    "Category": list(res["breakdown"].keys()),
    "Share (%)": list(shares.values()),
    "Amount (₹)": [f"{v:,.0f}" for v in res["breakdown"].values()],
})
st.table(table)

# Charts
pie = go.Figure(go.Pie(labels=list(res["breakdown"].keys()),
                       values=list(res["breakdown"].values()), hole=0.4))
pie.update_layout(title="Cost split by category")

bar = go.Figure(go.Bar(x=["Estimated cost", "Budget"], y=[total, budget],
                       marker_color=["#c62828" if diff < 0 else "#2e7d32", "#9aa5b1"]))
bar.update_layout(title="Estimate vs budget", yaxis_title="₹")

g1, g2 = st.columns(2)
g1.plotly_chart(pie, width="stretch")
g2.plotly_chart(bar, width="stretch")

# Sensitivity
st.subheader("What if the rate changes?")
rows = []
for change in (-10, 0, 10):
    r = rate * (1 + change / 100)
    cost = area * floors * r
    rows.append({"Rate change": f"{change:+d}%", "Rate (₹/sq ft)": f"{r:,.0f}",
                 "Total cost (₹)": f"{cost:,.0f}",
                 "Vs budget (₹)": f"{budget - cost:,.0f}"})
st.table(pd.DataFrame(rows))

with st.expander("Formulas and assumptions"):
    st.markdown("""
- Total built-up area = area per floor × number of floors
- Total cost = total built-up area × cost per sq ft
- Category amount = total cost × category share ÷ 100
- Difference = budget − estimated cost
- Category shares and the rate are sample, user-editable assumptions.
- This is a preliminary estimate, not a detailed quantity-based estimate.
    """)