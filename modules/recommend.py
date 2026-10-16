import math


def _num_ok(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def generate_recommendations(plot, cost, inputs, materials, layout=None,
                             quotation=None, parking=None, ventilation=None):
    """Rule-based recommendations (simple if/else checks, no AI model).
    Returns a list of (level, text). Levels: info, success, warning, error."""
    recs = []

    # ---- Plot ----
    if plot:
        util = plot["utilization"]
        recs.append(("info",
            f"Plot utilization is {util:.1f}%: {plot['buildable_area']:,.0f} sq ft is "
            f"buildable out of {plot['plot_area']:,.0f} sq ft. Setbacks remove "
            f"{plot['setback_area']:,.0f} sq ft. Confirm that the setbacks you entered "
            f"match your local rules."))
        if util < 50:
            recs.append(("warning",
                "Less than half of the plot is buildable with the entered setbacks. "
                "Re-check the setback values. If they are correct, building more than "
                "one floor can make better use of a small footprint."))
    else:
        recs.append(("warning", "Plot Analysis has not been completed yet."))

    # ---- Cost vs budget ----
    if cost and inputs:
        budget, rate = inputs["budget"], inputs["rate"]
        total = cost["total_cost"]
        diff = budget - total
        if diff < 0:
            pct = f" ({-diff / budget * 100:.1f}% over)" if budget > 0 else ""
            max_area = budget / rate if rate > 0 else 0
            recs.append(("error",
                f"The estimated cost exceeds your budget by ₹{-diff:,.0f}{pct}. At "
                f"₹{rate:,.0f}/sq ft, your budget covers about {max_area:,.0f} sq ft of "
                f"built-up area, against {cost['total_area']:,.0f} sq ft planned. "
                f"Options: reduce the area, reduce the floors, choose simpler finishes "
                f"(lower rate), or increase the budget."))
        else:
            margin = diff / budget * 100 if budget > 0 else 0
            if margin < 5:
                recs.append(("warning",
                    f"The estimate is within budget, but the margin is only "
                    f"₹{diff:,.0f} ({margin:.1f}%). Small rate changes could push the "
                    f"cost over the budget. Check the 'What if the rate changes?' table."))
            else:
                recs.append(("success",
                    f"The estimate is within budget, with ₹{diff:,.0f} ({margin:.1f}%) "
                    f"to spare. Consider keeping part of this as a reserve for "
                    f"unexpected costs."))
        top = max(cost["breakdown"], key=cost["breakdown"].get)
        recs.append(("info",
            f"The largest cost category is '{top}' at "
            f"₹{cost['breakdown'][top]:,.0f}. Savings here have the biggest effect."))
    else:
        recs.append(("warning", "Cost Estimator has not been completed yet."))

    # ---- Materials ----
    if materials and cost:
        if materials["total"] >= cost["total_cost"]:
            recs.append(("warning",
                "The material cost is as high as or higher than the total construction "
                "estimate, which is not consistent. Re-check the material factors and "
                "rates, or the cost per sq ft."))
        else:
            share = materials["total"] / cost["total_cost"] * 100
            recs.append(("info",
                f"The listed materials come to ₹{materials['total']:,.0f}, about "
                f"{share:.1f}% of the total construction estimate. Only four material "
                f"groups plus bricks are included, so this is not the full material cost."))
    else:
        recs.append(("warning", "Material Estimator has not been completed yet."))

    # ---- Layout ----
    if layout:
        recs.append(("info",
            f"Top-ranked concept layout: {layout['name']}, score {layout['total']:.1f} / 100, "
            f"built-up area {layout['footprint']:,.0f} sq ft, estimated cost ₹{layout['cost']:,.0f}. "
            f"Remember that it is a concept, not a drawing."))
        if not layout["fits"]:
            recs.append(("error",
                "No layout fits inside the buildable area with the current room list. Reduce "
                "the room sizes or counts, reduce the setbacks, or plan more than one floor."))
        failed = [r for r in layout["rooms"] if not r["ok"]]
        if failed:
            recs.append(("warning", "Rooms that fail a size or shape check in this layout: "
                         + "; ".join(f"{r['name']} ({r['issue']})" for r in failed) + "."))
        bad_rules = [r["rule"] for r in layout["rules"] if not r["ok"]]
        if bad_rules:
            recs.append(("warning", "Adjacency preferences not met: " + "; ".join(bad_rules) + "."))
        if inputs and layout["cost"] > inputs["budget"]:
            recs.append(("error",
                f"This layout's estimated cost is ₹{layout['cost'] - inputs['budget']:,.0f} above your "
                f"budget. Look at a more compact layout in the comparison table."))
        if cost and inputs:
            per_floor = cost["total_area"] / max(inputs.get("floors", 1), 1)
            if per_floor > 0 and abs(layout["footprint"] - per_floor) / per_floor > 0.10:
                recs.append(("info",
                    f"The layout's built-up area ({layout['footprint']:,.0f} sq ft) differs from the "
                    f"area used in the Cost Estimator ({per_floor:,.0f} sq ft per floor). Update the "
                    f"Cost Estimator area if you want the cost figures to match the layout."))
        if layout["fits"] and layout["util"] < 50:
            recs.append(("info",
                f"This layout uses {layout['util']:.0f}% of the buildable area, so there is room for "
                f"larger rooms or an extra room if the budget allows."))
        elif layout["fits"] and layout["util"] > 90:
            recs.append(("info",
                f"This layout uses {layout['util']:.0f}% of the buildable area, leaving little space "
                f"for open area or later extension."))
    else:
        recs.append(("info", "Layout Comparison has not been run yet, so there is no layout recommendation."))

    # ---- Quotation ----
    if quotation:
        c = quotation["counts"]
        first = [f for f in quotation["flags"] if f["Priority"] == "Check first"]
        if first:
            names = "; ".join(f["Item"] if f["Row"] == "-" else f"row {f['Row']} ({f['Item']})"
                              for f in first[:4])
            more = f" and {len(first) - 4} more" if len(first) > 4 else ""
            recs.append(("warning",
                f"The contractor quotation has {c['check_first']} item(s) to clarify first: {names}{more}. "
                f"Ask for a corrected, itemised quotation before agreeing to it. A flag is a question, "
                f"not proof of a mistake."))
        elif c["review"]:
            recs.append(("info",
                f"The quotation has {c['review']} item(s) to review (unusual rates or quantities, "
                f"or possible duplicates). Ask the contractor to explain them."))
        else:
            recs.append(("success",
                "The quotation checker raised no major flags with your settings. This does not "
                "guarantee that the quotation is correct."))
        sm = quotation["summary"]
        if sm.get("ref_items", 0) > 0 and sm.get("ref_at_ref", 0) > 0:
            d = sm["ref_quoted"] - sm["ref_at_ref"]
            recs.append(("info",
                f"For the {sm['ref_items']} quotation lines that have a reference rate, the quoted "
                f"rates are {d / sm['ref_at_ref'] * 100:+.1f}% compared with your reference rates."))
    else:
        recs.append(("info", "No contractor quotation has been checked yet."))

    # ---- Parking ----
    if parking:
        if parking["status"] == "Fits":
            recs.append(("success",
                f"Parking: {parking['vehicles']} vehicle(s) fit in {parking['space']} with the "
                f"clearances you entered (spare space {parking['margin']:.1f} ft)."))
        elif parking["status"] == "Fits, but tight":
            recs.append(("warning",
                f"Parking fits only just (spare space {parking['margin']:.1f} ft). Consider a wider or "
                f"longer space, and ask a professional to review the driveway and turning space."))
        else:
            recs.append(("error",
                f"Parking: the vehicle(s) do not fit in {parking['space']} with the clearances entered "
                f"(short by {abs(parking['margin']):.1f} ft). Enlarge the space or reduce the vehicles."))
    else:
        recs.append(("info", "Parking has not been assessed yet."))

    # ---- Ventilation ----
    if ventilation:
        if ventilation["rooms_review"] > 0:
            first_three = " ".join(ventilation["findings"][:3])
            recs.append(("warning",
                f"{ventilation['rooms_review']} of {ventilation['rooms_checked']} room(s) need review "
                f"for ventilation or daylight against your thresholds. {first_three}"))
        else:
            recs.append(("success",
                f"All {ventilation['rooms_checked']} room(s) meet the ventilation and daylight "
                f"thresholds you entered (indicator only)."))
    else:
        recs.append(("info", "Ventilation and daylight have not been assessed yet."))

    recs.append(("info",
        "All figures here are preliminary. Structural design, local building rules, fire safety, "
        "services and final drawings must be prepared and checked by qualified professionals."))
    return recs