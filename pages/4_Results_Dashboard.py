import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modules.recommend import generate_recommendations
from modules.report import build_html_report

st.title("Results Dashboard")

plot = st.session_state.get("plot_result")
cost = st.session_state.get("cost_result")
inputs = st.session_state.get("cost_inputs")
materials = st.session_state.get("material_result")
layout = st.session_state.get("layout_result")
ranking = st.session_state.get("layout_ranking")
quotation = st.session_state.get("quotation_result")
parking = st.session_state.get("parking_result")
ventilation = st.session_state.get("ventilation_result")

done = {"Plot Analysis": plot, "Cost Estimator": cost, "Material Estimator": materials,
        "Layout Comparison": layout, "Quotation Checker": quotation,
        "Parking": parking, "Ventilation and daylight": ventilation}

if not any(done.values()):
    st.warning("No results yet. Open the modules from the sidebar first (Plot Analysis, Cost Estimator, "
               "Material Estimator, Layout Comparison, Quotation Checker, Parking and Ventilation), "
               "then come back here.")
    st.stop()

st.caption("Results are kept only while this browser tab stays open. Refreshing the page clears them.")

# ---- Checklist -------------------------------------------------------------
st.markdown("**Modules completed:** " + "  ".join(
    f"{'✅' if v else '⬜'} {k}" for k, v in done.items()))

# ---- Key numbers -----------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
if plot:
    c1.metric("Buildable area", f"{plot['buildable_area']:,.0f} sq ft")
    c2.metric("Plot utilization", f"{plot['utilization']:.1f}%")
if cost and inputs:
    diff = inputs["budget"] - cost["total_cost"]
    c3.metric("Estimated cost", f"₹ {cost['total_cost']:,.0f}")
    c4.metric("Vs budget", f"₹ {diff:,.0f}", delta="within budget" if diff >= 0 else "over budget",
              delta_color="normal" if diff >= 0 else "inverse")

# ---- Cost and material charts ----------------------------------------------
g1, g2 = st.columns(2)
if cost:
    pie = go.Figure(go.Pie(labels=list(cost["breakdown"].keys()),
                           values=list(cost["breakdown"].values()), hole=0.4))
    pie.update_layout(title="Cost split by category")
    g1.plotly_chart(pie, width="stretch")
if materials:
    bar = go.Figure(go.Bar(x=[r["Material"] for r in materials["rows"]],
                           y=[r["Cost (₹)"] for r in materials["rows"]], marker_color="#2e7d32"))
    bar.update_layout(title="Material cost by item", yaxis_title="₹")
    g2.plotly_chart(bar, width="stretch")

# ---- Layout ----------------------------------------------------------------
if layout:
    st.subheader("Top-ranked concept layout")
    st.caption("Concept only, not an architectural drawing. Red outline = a room check failed.")
    l1, l2 = st.columns([3, 2])
    COLORS = {"Living room": "#ffe0b2", "Kitchen": "#c8e6c9", "Bedroom": "#bbdefb",
              "Bathroom": "#e1bee7", "Parking": "#cfd8dc"}
    fig = go.Figure()
    ex = max(r["x0"] + r["dx"] for r in layout["rooms"])
    ey = max(r["y0"] + r["dy"] for r in layout["rooms"])
    if plot:
        ex, ey = max(ex, plot["buildable_width"]), max(ey, plot["buildable_length"])
        fig.add_shape(type="rect", x0=0, y0=0, x1=plot["buildable_width"], y1=plot["buildable_length"],
                      line=dict(color="green", dash="dash", width=2))
    for r in layout["rooms"]:
        fig.add_shape(type="rect", x0=r["x0"], y0=r["y0"], x1=r["x0"] + r["dx"], y1=r["y0"] + r["dy"],
                      fillcolor=COLORS.get(r["type"], "#eee"),
                      line=dict(color="black" if r["ok"] else "red", width=1 if r["ok"] else 3))
        fig.add_annotation(x=r["x0"] + r["dx"] / 2, y=r["y0"] + r["dy"] / 2, showarrow=False,
                           text=f"{r['name']}<br>{r['dx']:.1f} × {r['dy']:.1f} ft",
                           font=dict(size=10, color="black"))
    fig.update_xaxes(range=[-1, ex + 1], title="Width (ft)")
    fig.update_yaxes(range=[-1, ey + 1], title="Length (ft)", scaleanchor="x", scaleratio=1)
    fig.update_layout(title=f"{layout['name']} (front of plot at the bottom)", height=480)
    l1.plotly_chart(fig, width="stretch")
    l2.metric("Layout score", f"{layout['total']:.1f} / 100")
    l2.metric("Built-up area", f"{layout['footprint']:,.0f} sq ft")
    l2.metric("Layout cost", f"₹ {layout['cost']:,.0f}")
    if ranking:
        l2.dataframe(pd.DataFrame([{"Rank": x["rank"], "Layout": x["name"], "Score": round(x["total"], 1)}
                                   for x in ranking]), hide_index=True)

# ---- Quotation, parking, ventilation status --------------------------------
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown("**Quotation check**")
    if quotation:
        cts = quotation["counts"]
        st.write(f"{quotation['summary']['n_items']} lines checked")
        st.write(f"🔴 Check first: {cts['check_first']}  🟠 Review: {cts['review']}  ⚪ Notes: {cts['note']}")
    else:
        st.write("Not run yet.")
with s2:
    st.markdown("**Parking**")
    if parking:
        icon = {"Fits": "✅", "Fits, but tight": "🟠", "Does not fit": "🔴"}[parking["status"]]
        st.write(f"{icon} {parking['status']} ({parking['vehicles']} vehicle(s), {parking['space']})")
    else:
        st.write("Not assessed yet.")
with s3:
    st.markdown("**Ventilation and daylight**")
    if ventilation:
        st.write(f"{ventilation['rooms_review']} of {ventilation['rooms_checked']} room(s) need review")
    else:
        st.write("Not assessed yet.")

# ---- Recommendations -------------------------------------------------------
st.subheader("Recommendations")
st.caption("These are RULE-BASED recommendations (simple if/else checks on your numbers). "
           "No AI model or machine learning is used.")
recs = generate_recommendations(plot, cost, inputs, materials, layout, quotation, parking, ventilation)
show = {"info": st.info, "success": st.success, "warning": st.warning, "error": st.error}
for level, text in recs:
    show[level](text)

# ---- Download --------------------------------------------------------------
st.subheader("Download summary report")
html = build_html_report(plot, cost, inputs, materials, recs, layout=layout, ranking=ranking,
                         quotation=quotation, parking=parking, ventilation=ventilation)
st.download_button("Download report (HTML)", data=html, file_name="AediPueblo_summary.html",
                   mime="text/html")
st.caption("Open the downloaded file in your browser, then press Ctrl + P and choose "
           "'Save as PDF' to get a PDF copy.")