# AediPueblo: demo script and checklist (about 7 minutes)

## Before you start (2 minutes)
- [ ] Close extra browser tabs. Stop and restart the app: `py -m streamlit run app.py`
- [ ] Open the app once and check the sidebar shows 7 pages
- [ ] Do NOT press F5 or refresh during the demo (it clears the results)
- [ ] Have the downloaded sample report (HTML or PDF) ready as a backup
- [ ] Keep the code folder open in VS Code in case you are asked to show it

## Run of show

| Min | Page | What to do | What to say |
|---|---|---|---|
| 0:00 | Home | Show the tagline and module list | "AediPueblo helps a homeowner do preliminary planning: plot, layout, cost, materials, quotation check. It is a planning aid, not a design or code-compliance tool." |
| 0:45 | Plot Analysis | Keep sample values; change the front setback from 10 to 15 | "Setbacks are entered by the user because they differ by place. I did not invent any rules. Notice the buildable area and utilization update and the plan view shows the buildable zone." |
| 1:45 | Cost Estimator | Show over-budget message; change cost per sq ft | "The area carries over automatically. Estimate is ₹92,000 over budget. The category split and the rate sensitivity table are editable assumptions." |
| 2:30 | Material Estimator | Show table and formulas expander | "Each quantity shows its formula. These are thumb rules, clearly labelled preliminary, not a bill of quantities." |
| 3:15 | Layout Comparison | Show ranking, score chart, open two plan tabs; set Bedrooms to 3 | "This is a real constraint-based search: it tries thousands of room orders and strip splits, filters by size and shape rules, then scores adjacency, budget and use of area. It is a heuristic, and not machine learning. The explanation says why rank 1 beats rank 2." |
| 4:30 | Quotation Checker | Show flags; point to row 8 (arithmetic) and steel rate | "Flags are questions to ask the contractor, not accusations. Each flag has a suggested question. It compares only against reference rates the user types in." |
| 5:30 | Parking and Ventilation | Switch vehicle to Large SUV to show 'does not fit'; show a room below threshold | "Clearances and thresholds are user-entered samples, not code values. Anything uncertain is flagged for professional review." |
| 6:15 | Results Dashboard | Show checklist, layout drawing, recommendations; click Download report | "Everything combines here. Recommendations are rule-based and labelled so. The report includes assumptions and limitations." |

## Questions you may be asked (honest answers)

**Is this AI?** No AI model or machine learning is used. The layout generator is a constraint-based heuristic search,
and recommendations are rule-based. An AI language model could be added later for explanations, clearly labelled.

**Is the best layout guaranteed?** No. It searches a large but limited set of strip arrangements, so it finds good
concept layouts, not guaranteed optimal ones.

**Are the costs and rates accurate?** They are sample values that the user edits. The tool does not know local rates.

**Does it follow building codes?** No. It does not assume or check local codes. Setbacks and thresholds are user inputs.

**Can I build from these layouts?** No. They are concepts. An architect and a structural engineer must prepare real drawings.

**Why does the quotation checker not say 'fraud'?** A difference can have many innocent causes (grade, scope, brand, a typing slip).
The tool only raises questions to ask.

**What would you improve next?** PDF quotation reading, multi-floor layouts, saved projects, local rule data, optional AI explanations.

## If something goes wrong during the demo
- Page shows an old result: stop the app (Ctrl + C), restart, and go through the pages again in order.
- Dashboard says "No results yet": the browser was refreshed. Visit the pages in order again.
- Red error message: take a screenshot and move on to the backup report.
