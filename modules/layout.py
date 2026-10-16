"""Preliminary layout comparison using a transparent constraint-based search.

Idea: rooms are packed into horizontal "bands" (strips) across the buildable
rectangle. The search tries many room orders and band splits, keeps only the
arrangements that satisfy the most size/shape constraints, then picks the one
with the best adjacency score. Several size levels and two band directions
give several candidate layouts, which are then scored and ranked.

These are concept layouts, NOT architectural drawings.
"""
import itertools
import random
from collections import Counter
from math import factorial

# SAMPLE room sizes. Editable assumptions, NOT building-code requirements.
DEFAULT_ROOMS = [
    {"Room": "Living room", "Count": 1, "Std area (sq ft)": 180,
     "Min area (sq ft)": 120, "Min short side (ft)": 10},
    {"Room": "Kitchen", "Count": 1, "Std area (sq ft)": 100,
     "Min area (sq ft)": 70, "Min short side (ft)": 7},
    {"Room": "Bedroom", "Count": 2, "Std area (sq ft)": 130,
     "Min area (sq ft)": 100, "Min short side (ft)": 9},
    {"Room": "Bathroom", "Count": 2, "Std area (sq ft)": 40,
     "Min area (sq ft)": 30, "Min short side (ft)": 5},
]

# Size levels: multiplier on the standard room areas (editable assumption).
SIZE_LEVELS = {"Compact": 0.85, "Standard": 1.00, "Spacious": 1.20}

# Scoring weights (they add up to 1.0).
WEIGHTS = {"requirements": 0.35, "design": 0.20, "budget": 0.25, "utilization": 0.20}
LABELS = {"requirements": "room size/shape checks", "design": "adjacency preferences",
          "budget": "budget fit", "utilization": "use of buildable area"}

EPS = 1e-6
MIN_CONTACT = 3.0   # ft of shared wall needed to count two rooms as adjacent


def build_rooms(room_rows, cars, bay_w, bay_l, factor, circulation):
    rooms = []
    for row in room_rows:
        n = int(row["Count"])
        for k in range(n):
            nominal = row["Std area (sq ft)"] * factor
            rooms.append({
                "name": row["Room"] if n == 1 else f"{row['Room']} {k + 1}",
                "type": row["Room"],
                "nominal": nominal,
                "draw": nominal * (1 + circulation / 100.0),
                "min_area": row["Min area (sq ft)"],
                "min_short": row["Min short side (ft)"],
                "min_long": 0.0,
                "parking": False,
            })
    if cars > 0:
        need_a, need_b = cars * bay_w, bay_l
        area = need_a * need_b
        rooms.append({
            "name": "Parking", "type": "Parking", "nominal": area, "draw": area,
            "min_area": 0.0, "min_short": min(need_a, need_b),
            "min_long": max(need_a, need_b), "parking": True,
            # (width along the band, minimum band depth): bay across or bay along
            "options": [(need_a, need_b), (need_b, need_a)],
        })
    return rooms


def _room_issue(room, h, w, max_aspect):
    short, long_ = (h, w) if h <= w else (w, h)
    if room["nominal"] + EPS < room["min_area"]:
        return "area below the minimum"
    if short + EPS < room["min_short"]:
        return f"short side {short:.1f} ft is below {room['min_short']:.1f} ft"
    if long_ + EPS < room["min_long"]:
        return f"long side {long_:.1f} ft is below {room['min_long']:.1f} ft"
    if not room["parking"] and long_ / short > max_aspect + EPS:
        return f"shape too long and thin ({long_ / short:.1f} : 1)"
    return ""


def _touch(a, b):
    ad0, as0, ah, aw = a
    bd0, bs0, bh, bw = b
    if abs(ad0 + ah - bd0) < EPS or abs(bd0 + bh - ad0) < EPS:
        if min(as0 + aw, bs0 + bw) - max(as0, bs0) >= MIN_CONTACT:
            return True
    if abs(as0 + aw - bs0) < EPS or abs(bs0 + bw - as0) < EPS:
        if min(ad0 + ah, bd0 + bh) - max(ad0, bd0) >= MIN_CONTACT:
            return True
    return False


def _design_rules(rects, rooms, orient):
    """Returns a list of (rule text, satisfied?)."""
    beds = [i for i, r in enumerate(rooms) if r["type"] == "Bedroom"]
    living = [i for i, r in enumerate(rooms) if r["type"] == "Living room"]
    out = []
    for i, r in enumerate(rooms):
        if r["type"] == "Bathroom" and beds:
            out.append((f"{r['name']} next to a bedroom",
                        any(_touch(rects[i], rects[j]) for j in beds)))
        elif r["type"] == "Kitchen" and living:
            out.append((f"{r['name']} next to the living room",
                        any(_touch(rects[i], rects[j]) for j in living)))
        elif r["parking"]:
            d0, s0, _, _ = rects[i]
            front = d0 if orient == "Rows" else s0
            out.append(("Parking at the front edge of the plot", front < EPS))
    return out


def _compositions(n, k):
    for cuts in itertools.combinations(range(1, n), k - 1):
        edges = (0,) + cuts + (n,)
        yield tuple(edges[i + 1] - edges[i] for i in range(k))


def _distinct_orders(rooms, limit=1500, seed=7):
    by_type = {}
    for i, r in enumerate(rooms):
        by_type.setdefault(r["type"], []).append(i)
    type_seq = [r["type"] for r in rooms]
    counts = Counter(type_seq)
    total = factorial(len(rooms))
    for c in counts.values():
        total //= factorial(c)

    def to_order(seq):
        used = {t: 0 for t in by_type}
        out = []
        for t in seq:
            out.append(by_type[t][used[t]])
            used[t] += 1
        return tuple(out)

    if total <= limit:
        res, cnt = [], dict(counts)

        def rec(prefix):
            if len(prefix) == len(rooms):
                res.append(to_order(prefix))
                return
            for t in cnt:
                if cnt[t] > 0:
                    cnt[t] -= 1
                    prefix.append(t)
                    rec(prefix)
                    prefix.pop()
                    cnt[t] += 1
        rec([])
        return res

    rng, seen, res = random.Random(seed), set(), []
    for _ in range(limit * 4):
        if len(res) >= limit:
            break
        s = type_seq[:]
        rng.shuffle(s)
        key = tuple(s)
        if key not in seen:
            seen.add(key)
            res.append(to_order(s))
    return res


def _band_geom(band, rooms, span):
    """Depth and room widths of one band, or None if the band is impossible.
    Normal rooms share the width in proportion to their area. A parking bay
    has a FIXED width (from the vehicle size) and can make the band deeper."""
    park = [i for i in band if rooms[i]["parking"]]
    others = [i for i in band if not rooms[i]["parking"]]
    s_oth = sum(rooms[i]["draw"] for i in others)
    if not park:
        return s_oth / span, {i: span * rooms[i]["draw"] / s_oth for i in band}
    p = park[0]
    best = None
    for pw, hmin in rooms[p]["options"]:
        if not others:
            cand = (max(hmin, rooms[p]["draw"] / span), {p: span})
        else:
            if pw >= span - 1.0:
                continue
            rest = span - pw
            h = max(hmin, s_oth / rest)
            widths = {p: pw}
            for i in others:
                widths[i] = rest * rooms[i]["draw"] / s_oth
            cand = (h, widths)
        if best is None or cand[0] < best[0]:
            best = cand
    return best


def _place(order, comp, rooms, span):
    rects, d0, pos = {}, 0.0, 0
    for size in comp:
        band = order[pos:pos + size]
        pos += size
        h, widths = _band_geom(band, rooms, span)
        s0 = 0.0
        for i in band:
            w = widths[i]
            rects[i] = (d0, s0, h, w)
            s0 += w
        d0 += h
    return rects, d0


def search_best(rooms, span, orient, max_aspect):
    """Tries many room orders and band splits. Keeps the arrangements that
    pass the most size/shape checks, then picks the best adjacency score
    (then the smallest footprint, then the most regular room shapes)."""
    n = len(rooms)
    ks = [k for k in (2, 3) if k <= n] or [1]
    comps = {c for k in ks for c in _compositions(n, k)}
    comps.add(tuple([1] * n))          # every room in its own band: always possible
    comps = sorted(comps)
    orders = _distinct_orders(rooms)
    band_memo = {}

    def band_info(band):
        if band not in band_memo:
            g = _band_geom(band, rooms, span)
            if g is None:
                band_memo[band] = None
            else:
                h, widths = g
                ok, shape = 0, 0.0
                for i in band:
                    w = widths[i]
                    if not _room_issue(rooms[i], h, w, max_aspect):
                        ok += 1
                    shape += max(h, w) / min(h, w)
                band_memo[band] = (ok, shape, h)
        return band_memo[band]

    scored = []
    for order in orders:
        for comp in comps:
            pos, ok, shape, depth, valid = 0, 0, 0.0, 0.0, True
            for size in comp:
                info = band_info(order[pos:pos + size])
                pos += size
                if info is None:
                    valid = False
                    break
                ok += info[0]
                shape += info[1]
                depth += info[2]
            if valid:
                scored.append((ok, -round(depth, 3), -shape, order, comp))
    best_ok = max(x[0] for x in scored)
    pool = sorted([x for x in scored if x[0] == best_ok],
                  key=lambda x: (x[1], x[2]), reverse=True)[:400]

    best, best_key = None, None
    for ok, neg_depth, neg_shape, order, comp in pool:
        rects, depth = _place(order, comp, rooms, span)
        rules = _design_rules(rects, rooms, orient)
        ratio = (sum(1 for _, s in rules if s) / len(rules)) if rules else 1.0
        key = (round(ratio, 6), neg_depth, neg_shape)
        if best_key is None or key > best_key:
            best_key, best = key, (rects, depth, rules)
    return best


def make_candidates(room_rows, cars, bay_w, bay_l, W, L, rate, budget,
                    circulation, max_aspect):
    cands = []
    for level, factor in SIZE_LEVELS.items():
        rooms = build_rooms(room_rows, cars, bay_w, bay_l, factor, circulation)
        for orient in ("Rows", "Columns"):
            span, avail = (W, L) if orient == "Rows" else (L, W)
            rects, depth, rules = search_best(rooms, span, orient, max_aspect)
            footprint = span * depth
            fits = depth <= avail + EPS
            placed, n_ok = [], 0
            for i, r in enumerate(rooms):
                d0, s0, h, w = rects[i]
                if orient == "Rows":
                    x0, y0, dx, dy = s0, d0, w, h
                else:
                    x0, y0, dx, dy = d0, s0, h, w
                issue = _room_issue(r, h, w, max_aspect)
                n_ok += 0 if issue else 1
                placed.append({"name": r["name"], "type": r["type"], "x0": x0,
                               "y0": y0, "dx": dx, "dy": dy, "area": dx * dy,
                               "ok": not issue, "issue": issue})
            cost = footprint * rate
            util = footprint / (W * L) * 100
            req = (int(fits) + n_ok) / (1 + len(rooms)) * 100
            design = (sum(1 for _, s in rules if s) / len(rules) * 100) if rules else 100.0
            overrun = (cost - budget) / budget * 100 if cost > budget else 0.0
            scores = {
                "requirements": req,
                "design": design,
                "budget": max(0.0, 100 - overrun * 4),
                "utilization": min(100.0, util) if fits else 0.0,
            }
            total = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)
            cands.append({
                "name": f"{level} / {orient}", "level": level, "orient": orient,
                "fits": fits, "depth": depth, "avail": avail,
                "footprint": footprint, "cost": cost, "util": util,
                "budget_diff": budget - cost, "rooms": placed,
                "rules": [{"rule": t, "ok": s} for t, s in rules],
                "scores": scores, "total": total,
            })
    cands.sort(key=lambda c: (not c["fits"], -c["total"]))
    for rank, c in enumerate(cands, 1):
        c["rank"] = rank
    return cands


def explain_ranking(ranked):
    feas = [c for c in ranked if c["fits"]]
    if not feas:
        return ["No layout fits inside the buildable area with these room sizes. "
                "Reduce the room list or sizes, reduce the setbacks, or use more floors."]
    best = feas[0]
    lines = [f"**{best['name']}** ranks first with {best['total']:.1f} / 100."]

    def compare(other, word):
        diffs = {k: WEIGHTS[k] * (best["scores"][k] - other["scores"][k]) for k in WEIGHTS}
        ups = sorted([(v, k) for k, v in diffs.items() if v > 0.5], reverse=True)[:2]
        downs = [(v, k) for k, v in diffs.items() if v < -0.5]
        if not ups and not downs:
            return (f"It is almost tied with {other['name']} ({other['total']:.1f}); "
                    "the differences are very small.")
        txt = f"Compared with {word} {other['name']} ({other['total']:.1f})"
        if ups:
            txt += ", it scores higher on " + " and ".join(
                f"{LABELS[k]} (+{v:.1f} pts)" for v, k in ups)
        if downs:
            txt += "; it scores lower on " + " and ".join(
                f"{LABELS[k]} ({v:.1f} pts)" for v, k in downs)
        return txt + "."

    if len(feas) > 1:
        lines.append(compare(feas[1], "the runner-up"))
    if len(feas) > 2:
        lines.append(compare(feas[-1], "the lowest-ranked fitting layout"))
    nofit = [c["name"] for c in ranked if not c["fits"]]
    if nofit:
        lines.append("Do not fit in the buildable area: " + ", ".join(nofit) + ".")
    return lines
    