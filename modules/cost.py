# Sample cost split (percent of total). These are EDITABLE ASSUMPTIONS,
# not standard values. Replace with your local data.
DEFAULT_CATEGORIES = {
    "Foundation & earthwork": 12,
    "Structure (columns, beams, slabs)": 30,
    "Masonry & plastering": 15,
    "Flooring & finishing": 18,
    "Doors & windows": 8,
    "Electrical": 7,
    "Plumbing & sanitary": 7,
    "Painting": 3,
}


def estimate_cost(area_per_floor, floors, rate, shares):
    """
    area_per_floor : sq ft
    floors         : number of floors
    rate           : cost per sq ft of built-up area
    shares         : dict {category: percent}, should add up to 100
    """
    total_area = area_per_floor * floors
    total_cost = total_area * rate
    breakdown = {name: total_cost * pct / 100 for name, pct in shares.items()}
    return {
        "total_area": total_area,
        "total_cost": total_cost,
        "breakdown": breakdown,
    }