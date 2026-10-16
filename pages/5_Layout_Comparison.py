import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.layout import (DEFAULT_ROOMS, SIZE_LEVELS, WEIGHTS, LABELS,
                            make_candidates, explain_ranking)

st.title("Layout Comparison")
st.warning("PRELIMINARY CONCEPT LAYOUTS ONLY. These are not architectural drawings, "
           "not code-compliant plans, and not construction-ready. Room sizes are "
           "SAMPLE values that you can edit.")

# ---- Inputs ----------------------------------------------------------------
plot = st.session_state.get("plot_result")
inputs = st.session_state.get("cost_inputs")
if plot:
    W0, L0 = float(plot["buildable_width"]), float(plot["buildable_length"])
    st.caption(f"Buildable rectangle taken from Plot Analysis: {W0:g} ft wide × {L0:g} ft long.")
else:
    W0, L0 = 32.0, 45.0
    st.caption("Tip: open Plot Analysis first to fill the buildable size automatically.")

c1, c2, c3, c4 = st.columns(4)
W = c1.number_input("Buildable width (ft)", min_value=0.0, value=W0, step=1.0)
L = c2.number_input("Buildable length (ft)", min_value=0.0, value=L0, step=1.0)
rate = c3.number_input("Cost per sq ft (₹)", min_value=0.0,
                       value=float(inputs["rate"]) if inputs else 1800.0, step=50.0)
budget = c4.number_input("Budget (₹)", min_value=0.0,
                         value=float(inputs["budget"]) if inputs else 2500000.0, step=50000.0)

st.subheader("Rooms (editable)")
rooms_df = st.data_editor(pd.DataFrame(DEFAULT_ROOMS), disabled=["Room"], hide_index=True,
                          column_config={"Count": st.column_config.NumberColumn(min_value=0, max_value=4, step=1)})

p1, p2, p3, p4, p5 = st.columns(5)
cars = p1.number_input("Cars to park", min_value=0, max_value=3, value=1, step=1)
bay_w = p2.number_input("Vehicle width (ft)", min_value=1.0, value=9.0, step=0.5,
                        help="Sample value. Use your vehicle's size plus clearance.")
bay_l = p3.number_input("Vehicle length (ft)", min_value=1.0, value=18.0, step=0.5)
circ = p4.number_input("Walls + circulation (%)", min_value=0.0, max_value=50.0, value=15.0, step=1.0,
                       help="Extra area added to room areas for walls and passages. Sample value.")
max_aspect = p5.number_input("Max room length : width", min_value=1.0, value=2.5, step=0.1,
                             help="Rooms longer and thinner than this are flagged.")

# ---- Validation ------------------------------------------------------------
if W <= 0 or L <= 0:
    st.error("Buildable width and length must be greater than zero.")
    st.stop()
if rate <= 0 or budget <= 0:
    st.error("Cost per sq ft and budget must be greater than zero.")
    st.stop()
rooms_df = rooms_df.fillna(0)
active = rooms_df[rooms_df["Count"] > 0]
if active.empty and cars == 0:
    st.error("Add at least one room or one parking space.")
    st.stop()
if (active[["Std area (sq ft)", "Min area (sq ft)", "Min short side (ft)"]] <= 0).any().any():
    st.error("Areas and minimum sides must be greater than zero for every room you use.")
    st.stop()
if (active["Std area (sq ft)"] < active["Min area (sq ft)"]).any():
    st.error("Standard area cannot be smaller than the minimum area.")
    st.stop()


@st.cache_data(show_spinner="Comparing layouts...")
def run(rows_json, cars, bay_w, bay_l, W, L, rate, budget, circ, max_aspect):
    return make_candidates(json.loads(rows_json), cars, bay_w, bay_l, W, L,
                           rate, budget, circ, max_aspect)


rows_json = json.dumps(active.to_dict("records"))
cands = run(rows_json, int(cars), bay_w, bay_l, W, L, rate, budget, circ, max_aspect)

std_total = float((active["Count"] * active["Std area (sq ft)"]).sum()) + cars * bay_w * bay_l
st.caption(f"Standard room areas + parking add up to about {std_total:,.0f} sq ft "
           f"(before walls and circulation). Buildable area: {W * L:,.0f} sq ft.")

# ---- Ranking ---------------------------------------------------------------
st.subheader("Ranking")
table = pd.DataFrame([{
    "Rank": c["rank"], "Layout": c["name"],
    "Fits?": "Yes" if c["fits"] else "No",
    "Built-up area (sq ft)": f"{c['footprint']:,.0f}",
    "Buildable area used (%)": f"{c['util']:.1f}",
    "Estimated cost (₹)": f"{c['cost']:,.0f}",
    "Vs budget (₹)": f"{c['budget_diff']:,.0f}",
    "Score (/100)": f"{c['total']:.1f}",
} for c in cands])
st.table(table)

for line in explain_ranking(cands):
    st.markdown("- " + line)

stack = go.Figure()
colors = {"requirements": "#1565c0", "design": "#6a1b9a", "budget": "#ef6c00", "utilization": "#2e7d32"}
for k in WEIGHTS:
    stack.add_trace(go.Bar(name=f"{LABELS[k]} ({WEIGHTS[k] * 100:.0f}%)",
                           x=[c["name"] for c in cands],
                           y=[WEIGHTS[k] * c["scores"][k] for c in cands],
                           marker_color=colors[k]))
stack.update_layout(barmode="stack", title="Score breakdown (weighted points, max 100)",
                    yaxis_title="Points")
st.plotly_chart(stack, width="stretch")

# ---- Plans -----------------------------------------------------------------
COLORS = {"Living room": "#ffe0b2", "Kitchen": "#c8e6c9", "Bedroom": "#bbdefb",
          "Bathroom": "#e1bee7", "Parking": "#cfd8dc"}


def plan_figure(c):
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=W, y1=L,
                  line=dict(color="green", dash="dash", width=2))
    for r in c["rooms"]:
        fig.add_shape(type="rect", x0=r["x0"], y0=r["y0"], x1=r["x0"] + r["dx"],
                      y1=r["y0"] + r["dy"], fillcolor=COLORS.get(r["type"], "#eeeeee"),
                      line=dict(color="black" if r["ok"] else "red", width=1 if r["ok"] else 3))
        fig.add_annotation(x=r["x0"] + r["dx"] / 2, y=r["y0"] + r["dy"] / 2, showarrow=False,
                           text=f"{r['name']}<br>{r['dx']:.1f} × {r['dy']:.1f} ft",
                           font=dict(size=10, color="black"))
    fig.update_xaxes(range=[-1, max(W, max(r['x0'] + r['dx'] for r in c['rooms'])) + 1],
                     title="Width (ft)")
    fig.update_yaxes(range=[-1, max(L, max(r['y0'] + r['dy'] for r in c['rooms'])) + 1],
                     title="Length (ft)", scaleanchor="x", scaleratio=1)
    fig.update_layout(title=f"{c['name']}: green dashed line = buildable area, "
                            f"front of the plot at the bottom", height=560)
    return fig


st.subheader("Layout plans")
tabs = st.tabs([f"#{c['rank']} {c['name']}" for c in cands])
for tab, c in zip(tabs, cands):
    with tab:
        if not c["fits"]:
            st.error(f"This layout needs {c['depth']:.1f} ft of depth but only "
                     f"{c['avail']:.1f} ft is available. It does not fit.")
        st.plotly_chart(plan_figure(c), width="stretch")
        st.markdown("**Room check** (red outline in the plan = a check failed)")
        st.table(pd.DataFrame([{
            "Room": r["name"], "Size (ft)": f"{r['dx']:.1f} × {r['dy']:.1f}",
            "Area (sq ft)": f"{r['area']:.0f}",
            "Check": "OK" if r["ok"] else r["issue"]} for r in c["rooms"]]))
        if c["rules"]:
            st.markdown("**Adjacency preferences**")
            for rule in c["rules"]:
                st.markdown(("✅ " if rule["ok"] else "❌ ") + rule["rule"])

st.session_state["layout_result"] = cands[0] if cands else None
st.session_state["layout_ranking"] = [
    {"rank": c["rank"], "name": c["name"], "fits": c["fits"], "total": c["total"],
     "cost": c["cost"], "footprint": c["footprint"]} for c in cands]

with st.expander("How the layouts are generated (algorithm, formulas, assumptions)"):
    st.markdown(f"""
**Search method (constraint-based, not machine learning).**
Rooms are packed into 2 or 3 *bands* (strips) across the buildable rectangle. The program
tries many room orders and band splits, in two directions (*Rows* = bands run across the
width, *Columns* = bands run along the length), and for each of the three size levels
({", ".join(f"{k} ×{v}" for k, v in SIZE_LEVELS.items())}). It keeps the arrangements that pass the most
room checks, then chooses the one with the best adjacency score, then the smallest built-up area.

**Formulas.** Band depth = total room area in the band ÷ band span. Room width = span × room area ÷ band area.
Room area used = standard area × size factor × (1 + walls/circulation %). A parking bay keeps a fixed
width from the vehicle size and may make its band deeper. Cost = built-up area × cost per sq ft.

**Room checks.** Area ≥ minimum area, short side ≥ minimum side, length : width ≤ limit,
parking bay ≥ vehicle size, and the whole layout must fit in the buildable rectangle.

**Adjacency preferences (design rules chosen for this tool, editable in code).**
Bathrooms next to a bedroom, kitchen next to the living room, parking at the front edge.
Two rooms count as adjacent if they share at least 3 ft of wall.

**Score (out of 100).** {", ".join(f"{LABELS[k]} {v * 100:.0f}%" for k, v in WEIGHTS.items())}.
Budget score drops 4 points for every 1% over budget. Utilization score = built-up area ÷ buildable area × 100.

**Limitations.** One floor level only, rectangular buildable area, rectangular rooms, no doors, windows,
stairs, structure or services, and no local-rule checks. Room sizes and rules are sample assumptions.
A qualified architect or engineer must prepare real plans.
""")