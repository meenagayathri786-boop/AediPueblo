import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from modules.quotation import (COLUMNS, SAMPLE_QUOTATION, SAMPLE_STATED_TOTAL,
                               check_quotation, map_columns)

st.title("Contractor Quotation Checker")
st.warning(
    "This tool only checks arithmetic, completeness, and differences from the reference "
    "rates YOU enter. A flag is a QUESTION to ask the contractor, not proof of a mistake or "
    "wrongdoing. Rates can differ for good reasons (brand, grade, scope, location, timing). "
    "The sample quotation below is made-up demonstration data.")

# ---- Settings --------------------------------------------------------------
s1, s2, s3 = st.columns(3)
rate_tol = s1.number_input("Rate difference to flag (%)", min_value=1.0, value=20.0, step=1.0,
                           help="Flag a rate that differs from your reference rate by more than this.")
qty_tol = s2.number_input("Quantity difference to flag (%)", min_value=1.0, value=15.0, step=1.0,
                          help="Flag a quantity that differs from your expected quantity by more than this.")
abs_tol = s3.number_input("Arithmetic tolerance (₹)", min_value=0.0, value=1.0, step=1.0,
                          help="Differences up to this amount are treated as rounding.")

# ---- Input table -----------------------------------------------------------
st.subheader("1. Enter or upload the quotation")
up = st.file_uploader("Upload a quotation as CSV or Excel (.xlsx). PDF is not supported in this version.",
                      type=["csv", "xlsx"])

source, base = "sample", pd.DataFrame(SAMPLE_QUOTATION)[COLUMNS]
default_total = SAMPLE_STATED_TOTAL
if up is not None:
    try:
        raw = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
        mapped, problems = map_columns(raw)
        if problems:
            st.error(" ".join(problems) + f" Columns found in your file: {', '.join(map(str, raw.columns))}. "
                     "Rename your columns to Item, Unit, Quantity, Rate, Amount and upload again. "
                     "Showing the sample instead.")
        else:
            source, base, default_total = f"upload_{up.name}", mapped, 0.0
            st.success(f"Loaded {len(mapped)} rows from {up.name}. Please check the table below.")
    except ImportError:
        st.error("Reading Excel files needs one more library. Run:  py -m pip install openpyxl")
    except Exception as e:
        st.error(f"Could not read that file ({type(e).__name__}). Check that it is a valid CSV or xlsx file.")

if source == "sample":
    st.caption("Showing a SAMPLE quotation with a few deliberate issues. Edit the table, add rows "
               "with the + at the bottom, or upload your own file.")
st.caption("'Reference rate' and 'Expected qty' are optional: type the rate you consider fair "
           "and, if you have it, the quantity from the Material Estimator.")

edited = st.data_editor(base, num_rows="dynamic", hide_index=True, key=f"q_{source}",
                        column_config={
                            "Quantity": st.column_config.NumberColumn(format="%g"),
                            "Rate (₹)": st.column_config.NumberColumn(format="%g"),
                            "Amount (₹)": st.column_config.NumberColumn(format="%g"),
                            "Reference rate (₹)": st.column_config.NumberColumn(format="%g"),
                            "Expected qty": st.column_config.NumberColumn(format="%g"),
                        })
stated = st.number_input("Total stated on the quotation (₹), optional", min_value=0.0,
                         value=float(default_total), step=1000.0,
                         help="Leave at 0 to skip this check.")

# ---- Run checks ------------------------------------------------------------
items, flags, sm = check_quotation(edited, stated, rate_tol, qty_tol, abs_tol)
if items.empty:
    st.warning("The table has no filled rows yet. Enter at least one item.")
    st.stop()

st.subheader("2. Results")
n_first = int((flags["Priority"] == "Check first").sum()) if not flags.empty else 0
n_rev = int((flags["Priority"] == "Review").sum()) if not flags.empty else 0
n_note = int((flags["Priority"] == "Note").sum()) if not flags.empty else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Lines checked", sm["n_items"])
m2.metric("Sum of quoted amounts", "n/a" if pd.isna(sm["quoted_total"]) else f"₹ {sm['quoted_total']:,.0f}")
m3.metric("Sum of quantity × rate", f"₹ {sm['calc_total']:,.0f}")
m4.metric("Flags", f"{len(flags)}", delta=f"{n_first} check first", delta_color="off")

if sm["ref_items"] > 0:
    d = sm["ref_quoted"] - sm["ref_at_ref"]
    pct = d / sm["ref_at_ref"] * 100 if sm["ref_at_ref"] else 0
    st.info(f"For the {sm['ref_items']} lines that have a reference rate: quoted rates give "
            f"₹{sm['ref_quoted']:,.0f}, your reference rates would give ₹{sm['ref_at_ref']:,.0f} "
            f"(quoted is {'+' if d >= 0 else '-'}₹{abs(d):,.0f}, {pct:+.1f}%). "
            f"This is only a comparison with your own reference values.")

PRIORITY_ICON = {"Check first": "🔴 Check first", "Review": "🟠 Review", "Note": "⚪ Note"}
if flags.empty:
    st.success("No flags were raised with the current settings. This does not guarantee the "
               "quotation is correct. It only means the checks above found nothing.")
else:
    show = flags.copy()
    show["Priority"] = show["Priority"].map(PRIORITY_ICON)
    show["Row"] = show["Row"].astype(str)
    st.markdown("**Flagged items** (each one explains what was found and what to ask)")
    st.dataframe(show, hide_index=True, width="stretch")
    st.download_button("Download flags (CSV)", flags.to_csv(index=False).encode("utf-8-sig"),
                       file_name="AediPueblo_quotation_flags.csv", mime="text/csv")

    st.markdown("**Rule-based summary** (simple if/else checks, not AI)")
    if n_first:
        top = flags[flags["Priority"] == "Check first"]
        st.markdown(f"- {n_first} item(s) to clarify first: "
                                        + "; ".join(i if r == "-" else f"row {r} ({i})" for r, i in zip(top["Row"], top["Item"])) + ".")
    if n_rev:
        st.markdown(f"- {n_rev} item(s) to review: unusual rates or quantities, or possible duplicates.")
    if n_note:
        st.markdown(f"- {n_note} minor note(s), such as a missing unit or similar descriptions.")
    st.markdown("- Ask the contractor for a corrected, itemised quotation and the reason for each "
                "flagged line before signing or paying anything.")

# ---- Charts ----------------------------------------------------------------
g1, g2 = st.columns(2)
dev = items[items["Rate vs ref (%)"].notna()]
if not dev.empty:
    colors = ["#c62828" if abs(v) > rate_tol else "#2e7d32" for v in dev["Rate vs ref (%)"]]
    fig = go.Figure(go.Bar(x=dev["Rate vs ref (%)"], y=dev["Item"], orientation="h",
                           marker_color=colors))
    fig.add_vline(x=rate_tol, line_dash="dash", line_color="gray")
    fig.add_vline(x=-rate_tol, line_dash="dash", line_color="gray")
    fig.update_layout(title="Quoted rate vs your reference rate (%)",
                      xaxis_title="Difference (%)", yaxis=dict(autorange="reversed"))
    g1.plotly_chart(fig, width="stretch")
else:
    g1.info("Enter reference rates in the table to see the rate comparison chart.")
if not flags.empty:
    counts = flags["Check"].value_counts()
    fig2 = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color="#ef6c00"))
    fig2.update_layout(title="Flags by type", yaxis_title="Number of flags")
    g2.plotly_chart(fig2, width="stretch")

# ---- Item table ------------------------------------------------------------
with st.expander("Line-by-line calculation"):
    t = items[["Row", "Item", "Unit", "Quantity", "Rate (₹)", "Amount (₹)", "Calc amount (₹)",
               "Amount diff (₹)", "Rate vs ref (%)", "Qty vs expected (%)"]].round(1)
    st.dataframe(t, hide_index=True, width="stretch")

st.session_state["quotation_result"] = {
    "summary": sm, "flags": flags.to_dict("records"),
    "counts": {"check_first": n_first, "review": n_rev, "note": n_note}}

with st.expander("What is checked, formulas and limitations"):
    st.markdown(f"""
**Checks (all simple rules)**
- **Missing entries:** empty description, missing or zero quantity or rate, missing amount or unit.
- **Arithmetic:** quantity × rate compared with the quoted amount (tolerance ₹{abs_tol:g}); sum of line amounts
  compared with sum of quantity × rate and with the total stated on the quotation.
- **Rate vs reference:** (quoted rate − reference rate) ÷ reference rate × 100, flagged above ±{rate_tol:g}%.
  Over twice that limit is marked "Check first". Reference rates are values you enter. They are not official rates.
- **Quantity vs expected:** same formula, flagged above ±{qty_tol:g}%.
- **Duplicates:** the same description after ignoring capitals and punctuation, or a very similar description
  (text similarity of 88% or more).

**Limitations.** Duplicates and similarity are found from item names only. The tool does not know local rates,
taxes, brands, specifications or site conditions. It cannot read PDF quotations in this version. A flag
never means a contractor is dishonest. Always discuss flagged lines with the contractor and, for important
decisions, have a qualified engineer or quantity surveyor review the quotation.
""")