from datetime import date
from html import escape
import math

TYPE_COLORS = {"Living room": "#ffe0b2", "Kitchen": "#c8e6c9", "Bedroom": "#bbdefb",
               "Bathroom": "#e1bee7", "Parking": "#cfd8dc"}


def _ok(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def _layout_svg(layout, plot):
    rooms = layout["rooms"]
    ex = max(max(r["x0"] + r["dx"] for r in rooms), plot["buildable_width"] if plot else 0)
    ey = max(max(r["y0"] + r["dy"] for r in rooms), plot["buildable_length"] if plot else 0)
    s = 420.0 / ex
    w, h = ex * s, ey * s
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w + 4:.0f}' height='{h + 4:.0f}' "
           f"viewBox='-2 -2 {w + 4:.0f} {h + 4:.0f}' style='border:1px solid #ccc;background:#fff'>"]
    if plot:
        out.append(f"<rect x='0' y='{h - plot['buildable_length'] * s:.1f}' "
                   f"width='{plot['buildable_width'] * s:.1f}' height='{plot['buildable_length'] * s:.1f}' "
                   f"fill='none' stroke='green' stroke-dasharray='6,4' stroke-width='2'/>")
    for r in rooms:
        x, y = r["x0"] * s, h - (r["y0"] + r["dy"]) * s
        rw, rh = r["dx"] * s, r["dy"] * s
        stroke = "#000" if r["ok"] else "#d00"
        out.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{rw:.1f}' height='{rh:.1f}' "
                   f"fill='{TYPE_COLORS.get(r['type'], '#eee')}' stroke='{stroke}' "
                   f"stroke-width='{1 if r['ok'] else 3}'/>")
        out.append(f"<text x='{x + rw / 2:.1f}' y='{y + rh / 2 - 2:.1f}' font-size='11' text-anchor='middle' "
                   f"font-family='Arial'>{escape(r['name'])}</text>")
        out.append(f"<text x='{x + rw / 2:.1f}' y='{y + rh / 2 + 11:.1f}' font-size='10' text-anchor='middle' "
                   f"font-family='Arial' fill='#333'>{r['dx']:.1f} x {r['dy']:.1f} ft</text>")
    out.append("</svg>")
    return "".join(out)


def build_html_report(plot, cost, inputs, materials, recs, layout=None, ranking=None,
                      quotation=None, parking=None, ventilation=None):
    def table(headers, rows):
        h = "".join(f"<th>{escape(str(x))}</th>" for x in headers)
        body = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
        return f"<table><tr>{h}</tr>{body}</table>"

    p = [
        "<html><head><meta charset='utf-8'><title>AediPueblo Summary</title>"
        "<style>body{font-family:Arial;margin:30px;max-width:900px;} "
        "table{border-collapse:collapse;margin-bottom:18px;} "
        "td,th{border:1px solid #999;padding:5px 9px;text-align:left;font-size:13px;} "
        "th{background:#e8f0e8;} h2{border-bottom:2px solid #2e7d32;padding-bottom:3px;margin-top:28px;} "
        ".note{background:#fff8e1;border:1px solid #f9a825;padding:8px;}</style></head><body>",
        "<h1>AediPueblo: Preliminary Summary</h1>",
        f"<p><i>Plan Smarter. Build Better.</i> Generated on {date.today()}</p>",
        "<p class='note'><b>Disclaimer:</b> Preliminary estimates only, based on sample and user-entered "
        "values. Not an approved plan, not a structural design, not a statement of code compliance and "
        "not construction-ready. Final decisions need review by qualified professionals.</p>",
    ]

    if plot:
        p.append("<h2>1. Plot analysis</h2>")
        p.append(table(["Item", "Value", "Unit"], [
            ["Plot area", f"{plot['plot_area']:,.1f}", "sq ft"],
            ["Buildable length", f"{plot['buildable_length']:,.1f}", "ft"],
            ["Buildable width", f"{plot['buildable_width']:,.1f}", "ft"],
            ["Buildable area", f"{plot['buildable_area']:,.1f}", "sq ft"],
            ["Plot utilization", f"{plot['utilization']:.1f}", "%"],
        ]))

    if cost and inputs:
        p.append("<h2>2. Cost estimate</h2>")
        p.append(f"<p>Area: {cost['total_area']:,.0f} sq ft, rate: ₹{inputs['rate']:,.0f}/sq ft, "
                 f"budget: ₹{inputs['budget']:,.0f}, estimated cost: ₹{cost['total_cost']:,.0f}, "
                 f"difference (budget − estimate): ₹{inputs['budget'] - cost['total_cost']:,.0f}</p>")
        p.append(table(["Category", "Amount (₹)"], [[k, f"{v:,.0f}"] for k, v in cost["breakdown"].items()]))

    if materials:
        p.append("<h2>3. Material quantities (preliminary)</h2>")
        p.append(table(["Material", "Quantity", "Unit", "Rate (₹)", "Cost (₹)"],
                       [[r["Material"], f"{r['Quantity']:,.0f}", r["Unit"], f"{r['Rate (₹)']:,.1f}",
                         f"{r['Cost (₹)']:,.0f}"] for r in materials["rows"]]))
        p.append(f"<p>Total material cost: ₹{materials['total']:,.0f}</p>")

    if layout:
        p.append("<h2>4. Concept layout comparison</h2>")
        if ranking:
            p.append(table(["Rank", "Layout", "Fits?", "Built-up area (sq ft)", "Cost (₹)", "Score (/100)"],
                           [[x["rank"], x["name"], "Yes" if x["fits"] else "No", f"{x['footprint']:,.0f}",
                             f"{x['cost']:,.0f}", f"{x['total']:.1f}"] for x in ranking]))
        p.append(f"<p><b>Top-ranked: {escape(layout['name'])}</b> (score {layout['total']:.1f} / 100), "
                 f"built-up area {layout['footprint']:,.0f} sq ft, estimated cost ₹{layout['cost']:,.0f}. "
                 f"This is a concept layout, not an architectural drawing. Front of the plot is at the bottom.</p>")
        p.append(_layout_svg(layout, plot))
        p.append(table(["Room", "Size (ft)", "Area (sq ft)", "Check"],
                       [[r["name"], f"{r['dx']:.1f} x {r['dy']:.1f}", f"{r['area']:.0f}",
                         "OK" if r["ok"] else r["issue"]] for r in layout["rooms"]]))
        if layout["rules"]:
            p.append("<p>Adjacency preferences: " + "; ".join(
                f"{escape(r['rule'])}: {'met' if r['ok'] else 'not met'}" for r in layout["rules"]) + "</p>")

    if quotation:
        sm = quotation["summary"]
        p.append("<h2>5. Contractor quotation check</h2>")
        qt = f"₹{sm['quoted_total']:,.0f}" if _ok(sm.get("quoted_total")) else "n/a"
        p.append(f"<p>Lines checked: {sm['n_items']}. Sum of quoted amounts: {qt}. Sum of quantity × rate: "
                 f"₹{sm['calc_total']:,.0f}. Flags: {len(quotation['flags'])}. Flags are questions to ask the "
                 f"contractor, not proof of errors or wrongdoing.</p>")
        if quotation["flags"]:
            p.append(table(["Row", "Item", "Priority", "Finding"],
                           [[f["Row"], f["Item"], f["Priority"], f["Finding"]] for f in quotation["flags"][:30]]))

    if parking:
        p.append("<h2>6. Parking check</h2>")
        p.append(table(["Item", "Value"], [
            ["Proposed space (width × length)", parking["space"]],
            ["Vehicles", f"{parking['vehicles']} ({parking['vehicle']} each)"],
            ["Best arrangement", parking["option"]],
            ["Result", parking["status"]],
            ["Smallest spare space", f"{parking['margin']:.1f} ft"],
        ]))

    if ventilation:
        p.append("<h2>7. Ventilation and daylight indicators</h2>")
        p.append(f"<p>{ventilation['rooms_review']} of {ventilation['rooms_checked']} room(s) marked for review. "
                 f"Thresholds used (entered by the user): daylight {ventilation['min_daylight']:g}% and "
                 f"ventilation {ventilation['min_vent']:g}% of floor area.</p>")
        if ventilation["findings"]:
            p.append("<ul>" + "".join(f"<li>{escape(f)}</li>" for f in ventilation["findings"]) + "</ul>")

    p.append("<h2>8. Recommendations (rule-based, not AI)</h2><ul>")
    p += [f"<li>{escape(text)}</li>" for _, text in recs]
    p.append("</ul>")
    p.append("<h2>9. Assumptions and limitations</h2><ul>"
             "<li>All rates, percentages, room sizes, clearances and thresholds are sample or user-entered values.</li>"
             "<li>Layouts are rectangular single-level concepts without doors, windows, stairs, structure or services.</li>"
             "<li>Material quantities use thumb rules and are not a detailed bill of quantities.</li>"
             "<li>Quotation flags only compare with the reference values the user entered.</li>"
             "<li>No local building rules, setbacks or code requirements were assumed or checked.</li>"
             "<li>No AI model or machine-learning model was used. Recommendations are simple rule-based checks.</li>"
             "</ul></body></html>")
    return "".join(p)