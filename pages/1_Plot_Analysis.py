
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.plot import analyze_plot

st.header("Plot Analysis")
st.caption("Evaluate plot dimensions and the preliminary building footprint.")

st.info(
    "Default values are sample values only. Enter the setbacks "
    "applicable to your site and local building regulations."
)

# --------------------------------------------------
# INPUTS
# --------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Plot dimensions")
    length = st.number_input(
        "Plot length (ft)", min_value=0.0,
        value=60.0, step=1.0, key="plot_length"
    )
    width = st.number_input(
        "Plot width (ft)", min_value=0.0,
        value=40.0, step=1.0, key="plot_width"
    )

with c2:
    st.subheader("Setbacks")
    front = st.number_input(
        "Front setback (ft)", min_value=0.0,
        value=10.0, step=0.5, key="plot_front"
    )
    rear = st.number_input(
        "Rear setback (ft)", min_value=0.0,
        value=5.0, step=0.5, key="plot_rear"
    )
    left = st.number_input(
        "Left setback (ft)", min_value=0.0,
        value=4.0, step=0.5, key="plot_left"
    )
    right = st.number_input(
        "Right setback (ft)", min_value=0.0,
        value=4.0, step=0.5, key="plot_right"
    )

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------
if length <= 0 or width <= 0:
    st.session_state.pop("plot_result", None)
    st.error("Plot length and width must be greater than zero.")
    st.stop()

buildable_length = length - front - rear
buildable_width = width - left - right

if buildable_length <= 0 or buildable_width <= 0:
    st.session_state.pop("plot_result", None)
    st.error(
        "The entered setbacks leave no positive rectangular "
        "area. Reduce the setbacks or verify the plot dimensions."
    )
    st.stop()

# --------------------------------------------------
# CALCULATION
# --------------------------------------------------
result = analyze_plot(length, width, front, rear, left, right)

if result is None:
    st.session_state.pop("plot_result", None)
    st.error("Plot analysis could not be completed. Check the inputs.")
    st.stop()

# Store successful results for the Results Dashboard.
st.session_state["plot_result"] = result

# --------------------------------------------------
# SUMMARY METRICS
# --------------------------------------------------
m1, m2, m3 = st.columns(3)

m1.metric("Total plot area", f"{result['plot_area']:,.1f} sq ft")
m2.metric("Remaining area", f"{result['buildable_area']:,.1f} sq ft")
m3.metric("Area utilization", f"{result['utilization']:.1f}%")

st.caption(
    "Remaining area is calculated after the entered setbacks. "
    "It does not establish legal building permission or permitted FSI."
)

# --------------------------------------------------
# DETAILED RESULTS
# --------------------------------------------------
st.subheader("Calculation details")

table = pd.DataFrame({
    "Measurement": [
        "Plot area",
        "Remaining length",
        "Remaining width",
        "Area remaining after setbacks",
        "Area excluded by setbacks",
        "Remaining-area ratio"
    ],
    "Value": [
        f"{result['plot_area']:,.1f}",
        f"{result['buildable_length']:,.1f}",
        f"{result['buildable_width']:,.1f}",
        f"{result['buildable_area']:,.1f}",
        f"{result['setback_area']:,.1f}",
        f"{result['utilization']:.1f}"
    ],
    "Unit": ["sq ft", "ft", "ft", "sq ft", "sq ft", "%"]
})

st.dataframe(table, hide_index=True, use_container_width=True)

# --------------------------------------------------
# CHART 1: AREA COMPARISON
# --------------------------------------------------
bar = go.Figure()

bar.add_trace(go.Bar(
    x=["Original plot", "Area after setbacks"],
    y=[result["plot_area"], result["buildable_area"]],
    marker_color=["#B7B9B0", "#78805A"],
    text=[
        f"{result['plot_area']:,.1f} sq ft",
        f"{result['buildable_area']:,.1f} sq ft"
    ],
    textposition="outside"
))

bar.update_layout(
    title="Plot area comparison",
    yaxis_title="Area (sq ft)",
    showlegend=False,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=20, r=20, t=60, b=30)
)

# --------------------------------------------------
# CHART 2: PLOT PLAN
# Front setback is shown at the bottom.
# --------------------------------------------------
plan = go.Figure()

# Outer plot
plan.add_shape(
    type="rect",
    x0=0, y0=0, x1=width, y1=length,
    line=dict(color="#343A34", width=2),
    fillcolor="#E9E9E2"
)

# Remaining rectangle
plan.add_shape(
    type="rect",
    x0=left, y0=front,
    x1=width - right, y1=length - rear,
    line=dict(color="#78805A", width=2),
    fillcolor="rgba(120,128,90,0.30)"
)

plan.add_annotation(
    x=width / 2,
    y=length / 2,
    text="AREA AFTER SETBACKS",
    showarrow=False,
    font=dict(color="#343A34", size=11)
)

plan.add_annotation(
    x=width / 2,
    y=front / 2,
    text="FRONT",
    showarrow=False,
    font=dict(color="#666666", size=10)
)

plan.update_xaxes(
    range=[-2, width + 2],
    title="Plot width (ft)",
    constrain="domain"
)

plan.update_yaxes(
    range=[-2, length + 2],
    title="Plot length (ft)",
    scaleanchor="x",
    scaleratio=1
)

plan.update_layout(
    title="Plot and setback diagram",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=20, r=20, t=60, b=35)
)

g1, g2 = st.columns(2)
g1.plotly_chart(bar, use_container_width=True)
g2.plotly_chart(plan, use_container_width=True)

st.warning(
    "Preliminary planning estimate only. Actual permitted building "
    "coverage, setbacks, FSI/FAR and other requirements depend on "
    "applicable local regulations and site conditions."
)
