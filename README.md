# AediPueblo

**Plan Smarter. Build Better.**

AediPueblo is a preliminary residential planning tool for homeowners and small property owners.
It combines plot analysis, concept layout comparison, cost and material estimation, a contractor
quotation checker, and parking and ventilation indicators in one Streamlit web application.

> **Important.** AediPueblo produces *preliminary estimates and concept layouts only*. It does not
> produce construction-ready drawings, does not check structural safety or building-code compliance,
> and does not assume any local setbacks or regulations. All rates, percentages, room sizes,
> clearances and thresholds are **sample values that the user must replace**. Final designs and
> construction decisions require review by qualified professionals.

## What is (and is not) "AI" here

* **No AI model, no machine learning, and no external API is used.**
* The layout generator is a **transparent, constraint-based heuristic search** (explained below).
* Recommendations are **rule-based** (plain if/else checks on the calculated numbers) and are labelled as such in the app.

## Modules

| Page | What it does |
|---|---|
| Plot Analysis | Plot area, user-entered setbacks, buildable area, utilization %, table and charts |
| Cost Estimator | Area × floors × rate, editable cost categories, comparison with budget, rate sensitivity (±10%) |
| Material Estimator | Cement, sand, aggregate, steel (thumb rules per sq ft) and bricks (wall-volume method), with formulas shown |
| Layout Comparison | Generates and ranks 6 concept layouts (3 size levels × 2 band directions), draws them, explains the ranking |
| Quotation Checker | Enter or upload (CSV/Excel) a quotation; checks arithmetic, missing entries, rates vs your reference rates, quantities, duplicates |
| Parking and Ventilation | Vehicle-in-space fit check; window-to-floor and openable-to-floor ratios against thresholds you enter |
| Results Dashboard | Combines all results, rule-based recommendations, downloadable HTML report (print to PDF) |

## How to run

1. Install Python 3.11 or newer.
2. Install the libraries:
   ```
   py -m pip install -r requirements.txt
   ```
3. Start the app from the project folder:
   ```
   py -m streamlit run app.py
   ```
4. Open `http://localhost:8501`. Use the pages in the sidebar from top to bottom, then open the
   Results Dashboard. Do not refresh the browser between pages: results are kept in the browser
   session only and a refresh clears them.

## Project structure

```
AediPueblo/
├── app.py                      home page and navigation
├── requirements.txt
├── modules/
│   ├── plot.py                 plot and setback calculations
│   ├── cost.py                 cost estimate and category split
│   ├── materials.py            material quantity methods
│   ├── layout.py               constraint-based layout search, scoring, ranking
│   ├── quotation.py            quotation checks
│   ├── checks.py               parking fit and ventilation / daylight indicators
│   ├── recommend.py            rule-based recommendations
│   └── report.py               HTML report builder
└── pages/                      one Streamlit page per module
```

## Key methods and formulas

**Plot.** Buildable length = length − front − rear setback. Buildable width = width − left − right setback.
Buildable area = buildable length × buildable width. Utilization = buildable area ÷ plot area × 100.

**Cost.** Total cost = area per floor × floors × rate. Category amount = total × share ÷ 100.
Difference = budget − estimate.

**Materials.** Thumb-rule items: quantity = built-up area × factor. Bricks: wall length × height ×
(thickness ÷ 12) × (1 − openings %) × bricks per cu ft. Cost = quantity × rate.

**Layouts.** Rooms are packed into 2 or 3 horizontal bands across the buildable rectangle (bands run
across the width or along the length). Room widths in a band are proportional to room area. A parking
bay has a fixed width from the vehicle size and may deepen its band. The search tries many room orders
and band splits and keeps the arrangements that pass the most room checks (minimum area, minimum side,
length-to-width limit, parking bay size), then picks the best adjacency result (bathroom next to a
bedroom, kitchen next to the living room, parking at the front), then the smallest footprint.
Each of three size levels (Compact ×0.85, Standard ×1.0, Spacious ×1.2) and each of two band directions
gives one candidate, so six layouts are ranked. Score (out of 100) = 35% room checks + 20% adjacency +
25% budget fit + 20% use of buildable area. The search is a heuristic: it does not guarantee the
mathematically best layout.

**Quotation.** Flags: missing entries; quantity × rate ≠ amount; sum of lines ≠ stated total; rate differing
from the user's reference rate by more than a chosen percentage; quantity differing from an expected
quantity; exact or similar duplicate descriptions. Every flag includes a suggested question for the
contractor. A flag is a question, never an accusation.

**Parking and ventilation.** Needed parking size = vehicle size + user-entered clearances, tested in both
orientations and (for several vehicles) side by side or one behind the other. Window-to-floor % = window
area ÷ floor area × 100. Openable-to-floor % = window area × openable share ÷ floor area × 100. Both are
compared with thresholds entered by the user.

## Sample inputs for a quick demonstration

Plot 60 × 40 ft, setbacks 10 / 5 / 4 / 4 ft (front / rear / left / right), cost ₹1,800 per sq ft,
budget ₹25,00,000. The defaults in every page already match these values.

Expected results with the sample inputs:

* Plot area 2,400 sq ft, buildable area 1,440 sq ft, utilization 60%
* Estimated cost ₹25,92,000, which is ₹92,000 over the budget
* Layout Comparison: 6 layouts, top-ranked Spacious / Rows with a score near 94
* Quotation Checker (sample quotation): 11 lines, 7 flags (arithmetic error in row 8, missing quantity in row 11,
  total mismatch, steel rate 38% above the reference rate, sand quantity above expected, duplicate cement, line-sum difference)
* Parking: one small vehicle fits with about 1.9 ft spare in the top layout's parking space
* Ventilation (sample rooms): kitchen, bedroom 1 and bathroom marked for review

## Limitations

* Setbacks, room sizes, clearances, thresholds and rates are user-editable sample values, not official figures.
* Layouts are rectangular, single-level concepts with no doors, windows, stairs, structure or services.
* The number of floors is used in the cost estimate only; layouts represent one floor level.
* Material quantities are thumb-rule estimates, not a bill of quantities.
* Quotation checks use only the reference rates the user enters; PDF quotations cannot be read in this version.
* Parking checks do not assess turning space, ramps or gate swing. Ventilation checks do not consider sun
  direction, shading or mechanical ventilation.
* Results exist only while the browser tab stays open.

## Possible future work

PDF quotation reading, multi-floor layouts, local rule packs entered as editable data, saving and loading
projects, and an optional AI language model for natural-language explanations (only if an API is configured
and clearly labelled).
