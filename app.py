import streamlit as st
from pathlib import Path

# =========================================================
# AEDIPUEBLO: HOME PLANNING FOR EVERYONE
# Requires Streamlit 1.39 or newer (keyed containers).
# =========================================================

st.set_page_config(
    page_title="AediPueblo | Home Planning Studio",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Soft, light colours for every chart in the app (see chart_theme.py)
try:
    from chart_theme import apply_chart_theme
    apply_chart_theme()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
ASSET_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSET_DIR / "aedipueblo_logo.svg"
MARK_PATH = ASSET_DIR / "aedipueblo_mark.svg"


def html(markup: str):
    """Render HTML without markdown mistaking indented lines for code."""
    clean = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


# ---------------------------------------------------------
# LOGO
# An arched doorway (a home's entrance) holding a small village
# of three houses under a rising sun. "Aedi" = house,
# "Pueblo" = village / people. The dotted arch is a nod to
# blueprint drafting lines.
# ---------------------------------------------------------
MARK_INNER = """
<path d="M10 112 V56 a50 50 0 0 1 100 0 V112 Z" fill="#14504B"/>
<path d="M16 112 V58 a44 44 0 0 1 88 0 V112" fill="none" stroke="#9CC9BF"
      stroke-width="1.3" stroke-dasharray="2 3.2" opacity="0.75"/>
<circle cx="60" cy="34" r="8" fill="#E5A82B"/>
<g stroke="#E5A82B" stroke-width="2" stroke-linecap="round">
  <path d="M72 34h5M70.4 28l4.3-2.5M66 23.6l2.5-4.3M60 22v-5M54 23.6l-2.5-4.3M49.6 28l-4.3-2.5M48 34h-5"/>
</g>
<g fill="#CFE5DE">
  <path d="M14 82 L29 68 L44 82 V100 H14 Z"/>
  <path d="M76 82 L91 68 L106 82 V100 H76 Z"/>
</g>
<g fill="#EAF3EF" stroke="#14504B" stroke-width="2.2" stroke-linejoin="round">
  <path d="M38 69 L60 46 L82 69 V100 H38 Z"/>
</g>
<g fill="#14504B">
  <rect x="45" y="74" width="7" height="7" rx="1"/>
  <rect x="68" y="74" width="7" height="7" rx="1"/>
  <rect x="26.5" y="86" width="5" height="5" rx="1"/>
  <rect x="88.5" y="86" width="5" height="5" rx="1"/>
</g>
<path d="M54 100 V91 a6 6 0 0 1 12 0 V100 Z" fill="#E5A82B"/>
<path d="M10 100 H110" stroke="#E5A82B" stroke-width="2.2" stroke-linecap="round"/>
<path d="M10 106 H110" stroke="#9CC9BF" stroke-width="1" opacity="0.6"/>
"""

LOGO_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="340" height="96"
     viewBox="0 0 340 96" role="img" aria-label="AediPueblo logo">
  <g transform="translate(2 3) scale(0.77)">{MARK_INNER}</g>
  <text x="108" y="54" font-family="Fraunces, Georgia, serif" font-size="35"
        letter-spacing="-0.8"><tspan font-weight="600" fill="#14504B">Aedi</tspan><tspan
        font-weight="400" fill="#10302E">Pueblo</tspan></text>
  <path d="M110 64 H150" stroke="#E5A82B" stroke-width="2.4" stroke-linecap="round"/>
  <text x="110" y="82" font-family="Figtree, Arial, sans-serif" font-size="13.5"
        letter-spacing="0.3" fill="#55696A">Home planning for everyone</text>
</svg>"""

MARK_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"
     viewBox="0 0 120 120" role="img" aria-label="AediPueblo mark">{MARK_INNER}</svg>"""

try:
    ASSET_DIR.mkdir(exist_ok=True)
    LOGO_PATH.write_text(LOGO_SVG, encoding="utf-8")
    MARK_PATH.write_text(MARK_SVG, encoding="utf-8")
except OSError:
    pass  # read-only hosting: the inline logo below still works


# ---------------------------------------------------------
# DESIGN SYSTEM
# Deep teal (planning ink) + marigold (the one warm accent)
# on a cool, clean off-white. Fraunces for headings, Figtree
# for everything you read.
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&display=swap');

:root {
    --bg: #FBFCFA;
    --card: #FFFFFF;
    --ink: #173E3A;
    --teal: #2F7A6E;
    --teal-deep: #173E3A;
    --marigold: #EDBB55;
    --marigold-soft: #FDF6E3;
    --chalk: #F1F6F3;
    --line: #E3EBE7;
    --muted: #5E7270;
}

.stApp {
    background: var(--bg);
    color: var(--ink);
    font-family: 'Figtree', sans-serif;
}

.block-container {
    max-width: 1240px;
    padding-top: 2.5rem;
    padding-bottom: 1.5rem;
}

h1, h2, h3, h4 {
    font-family: 'Fraunces', Georgia, serif;
    color: var(--ink);
    letter-spacing: -0.4px;
}

p, label, li, [data-testid="stMarkdownContainer"] {
    font-family: 'Figtree', sans-serif;
}

footer { visibility: hidden; }

*:focus-visible {
    outline: 3px solid var(--marigold);
    outline-offset: 2px;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: var(--chalk);
    border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] hr { border-color: var(--line); }
section[data-testid="stSidebar"] a { border-radius: 8px; }
.side-title {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 18px;
    font-weight: 500;
    color: var(--ink);
    margin: 4px 0 6px;
}
.side-copy {
    font-size: 13.5px;
    line-height: 1.7;
    color: var(--muted);
}

/* ---------- Hero ---------- */
.st-key-hero {
    background-color: #EAF3EF;
    background-image:
        linear-gradient(rgba(47,122,110,0.07) 1px, transparent 1px),
        linear-gradient(90deg, rgba(47,122,110,0.07) 1px, transparent 1px),
        linear-gradient(135deg, #F3F8F5 0%, #E2EFE9 100%);
    background-size: 28px 28px, 28px 28px, 100% 100%;
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 46px 46px 42px;
    margin-bottom: 44px;
}
.hero-title {
    font-family: 'Fraunces', Georgia, serif;
    font-size: clamp(34px, 4.6vw, 56px);
    font-weight: 500;
    line-height: 1.1;
    letter-spacing: -1.2px;
    color: var(--ink);
    margin: 0 0 18px;
}
.hero-copy {
    max-width: 520px;
    font-size: 16.5px;
    line-height: 1.75;
    color: #4B6361;
    margin-bottom: 26px;
}
.hero-note {
    font-size: 13.5px;
    color: var(--muted);
    margin-top: 14px;
}
.st-key-hero [data-testid^="stPageLink"] a,
.st-key-hero a[data-testid^="stPageLink"] {
    display: inline-flex;
    background: var(--teal) !important;
    border-radius: 999px;
    padding: 12px 28px !important;
    text-decoration: none !important;
    transition: background 0.2s ease;
}
.st-key-hero [data-testid^="stPageLink"] a:hover,
.st-key-hero a[data-testid^="stPageLink"]:hover {
    background: #256A5F !important;
}
.st-key-hero [data-testid^="stPageLink"] p,
.st-key-hero a[data-testid^="stPageLink"] p {
    color: #FFFFFF !important;
    font-weight: 700;
    font-size: 15.5px;
    margin: 0;
}

/* ---------- Section headings ---------- */
.section-heading {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 30px;
    font-weight: 500;
    color: var(--ink);
    margin: 0 0 6px;
}
.section-description {
    color: var(--muted);
    font-size: 15.5px;
    line-height: 1.7;
    max-width: 620px;
    margin-bottom: 24px;
}

/* ---------- Tool cards ---------- */
[class*="st-key-card-"] {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 22px 22px 14px;
    min-height: 212px;
    margin-bottom: 6px;
    box-shadow: 0 1px 2px rgba(23,62,58,0.04),
                0 12px 28px -18px rgba(23,62,58,0.18);
    transition: border-color 0.2s ease;
}
[class*="st-key-card-"]:hover { border-color: #9CC9BF; }

.card-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: #EAF3EF;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}
.card-icon svg {
    width: 23px;
    height: 23px;
    fill: none;
    stroke: var(--teal);
    stroke-width: 1.7;
    stroke-linecap: round;
    stroke-linejoin: round;
}
.card-title {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 21px;
    font-weight: 500;
    color: var(--ink);
    margin-bottom: 6px;
}
.card-copy {
    font-size: 14.5px;
    line-height: 1.65;
    color: var(--muted);
    min-height: 48px;
}

/* Quiet "Open" links inside cards */
[class*="st-key-card-"] [data-testid^="stPageLink"] a,
.st-key-ai-strip [data-testid^="stPageLink"] a {
    padding: 4px 0 !important;
    background: transparent !important;
    text-decoration: none !important;
}
[class*="st-key-card-"] [data-testid^="stPageLink"] p,
.st-key-ai-strip [data-testid^="stPageLink"] p {
    color: var(--teal) !important;
    font-weight: 700;
    font-size: 14.5px;
    margin: 0;
}
[class*="st-key-card-"] [data-testid^="stPageLink"] a:hover p,
.st-key-ai-strip [data-testid^="stPageLink"] a:hover p {
    text-decoration: underline;
}

/* ---------- Aedi AI strip ---------- */
.st-key-ai-strip {
    background: var(--marigold-soft);
    border-left: 5px solid var(--marigold);
    border-radius: 0 14px 14px 0;
    padding: 20px 26px 12px;
    margin: 26px 0 8px;
}
.ai-title {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 21px;
    font-weight: 500;
    color: var(--ink);
    margin-bottom: 4px;
}
.ai-copy {
    font-size: 15px;
    color: #5A5238;
    line-height: 1.65;
}

/* ---------- Suggested path (a real sequence) ---------- */
.path {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
    margin-top: 6px;
}
.path-step {
    border-top: 3px solid var(--teal);
    padding-top: 14px;
}
.path-num {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 26px;
    color: var(--teal);
    margin-bottom: 4px;
}
.path-name {
    font-weight: 700;
    font-size: 15.5px;
    color: var(--ink);
    margin-bottom: 4px;
}
.path-copy {
    font-size: 14px;
    line-height: 1.65;
    color: var(--muted);
}

/* ---------- Disclaimer and footer ---------- */
.disclaimer {
    color: var(--muted);
    font-size: 13.5px;
    line-height: 1.75;
    padding: 20px 0;
    border-top: 1px solid var(--line);
    margin-top: 40px;
}
.footer {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 10px;
    padding: 6px 0 10px;
    color: #6F8280;
    font-size: 12.5px;
}
.footer strong { color: var(--ink); font-weight: 600; }

@media (max-width: 800px) {
    .st-key-hero { padding: 28px 22px; }
    .path { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 520px) {
    .path { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# ICONS (simple line icons, one per tool)
# ---------------------------------------------------------
ICONS = {
    "plot": '<path d="M4 7l8-3 8 4-2 11-12 1z"/><path d="M9 11l5-1 1 5-5 1z"/>',
    "cost": '<path d="M7 5h10M7 9h10M7 5c5 0 7 2 7 4s-2 4-7 4l7 6"/>',
    "materials": '<path d="M3 6h18v4H3zM3 10h18v4H3zM3 14h18v4H3z"/><path d="M9 6v4M15 10v4M9 14v4"/>',
    "layout": '<path d="M4 4h16v16H4z"/><path d="M4 12h9M13 4v16M13 15h7"/>',
    "quote": '<path d="M6 3h9l4 4v14H6z"/><path d="M9 13l2 2 4-4"/>',
    "air": '<path d="M3 8h10a3 3 0 1 0-3-3"/><path d="M3 13h15a3 3 0 1 1-3 3"/>',
    "summary": '<path d="M4 20V10M10 20V4M16 20v-8M2 20h20"/>',
}


def icon(name: str) -> str:
    return f'<div class="card-icon"><svg viewBox="0 0 24 24">{ICONS[name]}</svg></div>'


# ---------------------------------------------------------
# TOOLS
# ---------------------------------------------------------
MODULES = [
    {
        "id": "plot",
        "title": "Know your plot",
        "description": "Enter your plot size and see how much of it you can build on.",
        "path": "pages/1_Plot_Analysis.py",
    },
    {
        "id": "cost",
        "title": "Estimate your cost",
        "description": "See what your house may cost and whether it fits your budget.",
        "path": "pages/2_Cost_Estimator.py",
    },
    {
        "id": "materials",
        "title": "Plan your materials",
        "description": "Get approximate quantities and costs of construction materials.",
        "path": "pages/3_Materials_Estimator.py",
    },
    {
        "id": "layout",
        "title": "Compare layouts",
        "description": "Find out which layout idea suits your family's needs best.",
        "path": "pages/5_Layout_Comparison.py",
    },
    {
        "id": "quote",
        "title": "Check your quotation",
        "description": "Spot arithmetic mistakes and unusual rates in a contractor's quote.",
        "path": "pages/6_Quotation_Checker.py",
    },
    {
        "id": "air",
        "title": "Parking and airflow",
        "description": "Check that your cars fit and that rooms get air and daylight.",
        "path": "pages/7_Parking_Ventilation.py",
    },
    {
        "id": "summary",
        "title": "See your summary",
        "description": "View all your results together, with recommendations and a report.",
        "path": "pages/4_Results_Dashboard.py",
    },
]

HERO_ART = """
<svg viewBox="0 0 440 320" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Line drawing of a house with measurements"
     style="width:100%;height:auto;display:block">
  <circle cx="368" cy="62" r="22" fill="#EDBB55" fill-opacity="0.85"/>
  <path d="M70 146 L220 52 L370 146 Z" fill="#CFE5DE" fill-opacity="0.75"/>
  <path d="M90 140 H350 V262 H90 Z" fill="#FFFFFF" fill-opacity="0.8"/>
  <g fill="none" stroke="#3F8A7D" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
    <path d="M40 262 H400"/>
    <path d="M90 262 V140 H350 V262"/>
    <path d="M70 146 L220 52 L370 146"/>
    <path d="M125 190 h58 v42 h-58 z"/>
    <path d="M154 190 v42 M125 211 h58"/>
    <path d="M262 190 h58 v42 h-58 z"/>
    <path d="M292 190 v42 M262 211 h58"/>
  </g>
  <path d="M200 262 V224 a20 20 0 0 1 40 0 V262 Z" fill="#EDBB55"/>
  <g fill="none" stroke="#7FB5A8" stroke-width="1.2">
    <path d="M90 286 H350 M90 280 v12 M350 280 v12"/>
    <path d="M394 140 V262 M388 140 h12 M388 262 h12"/>
  </g>
  <g font-family="Figtree, Arial, sans-serif" font-size="13" fill="#4B6361">
    <rect x="195" y="277" width="50" height="18" fill="#E9F2EE"/>
    <text x="220" y="291" text-anchor="middle">30 ft</text>
    <text x="406" y="205" transform="rotate(90 406 205)" text-anchor="middle">20 ft</text>
  </g>
</svg>
"""


def tool_card(module: dict):
    try:
        box = st.container(key=f"card-{module['id']}")
    except TypeError:  # older Streamlit without keyed containers
        box = st.container()
    with box:
        html(f"""
        {icon(module["id"])}
        <div class="card-title">{module["title"]}</div>
        <div class="card-copy">{module["description"]}</div>
        """)
        st.page_link(module["path"], label="Open")


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------
def home():

    # Sidebar brand
    with st.sidebar:
        html(LOGO_SVG)
        st.markdown("---")
        html("""
        <div class="side-title">Your project, in one place</div>
        <div class="side-copy">
            A planning workspace for homeowners and small property owners.
            Early estimates, explained simply.
        </div>
        """)

    # Hero
    with st.container(key="hero"):
        left, right = st.columns([1.1, 1], gap="large", vertical_alignment="center")
        with left:
            html("""
            <div class="hero-title">Plan your home before you build it.</div>
            <div class="hero-copy">
                Check your plot, estimate costs, compare layouts and review
                contractor quotations, step by step and in plain language.
            </div>
            """)
            st.page_link("pages/1_Plot_Analysis.py", label="Start with your plot")
            html('<div class="hero-note">Early estimates to help you plan and ask better questions.</div>')
        with right:
            html(HERO_ART)

    # Tools
    html("""
    <div class="section-heading">Everything you need to plan</div>
    <div class="section-description">
        Open the tool that matches your question today, or work through
        them in order.
    </div>
    """)

    for start in range(0, len(MODULES), 3):
        columns = st.columns(3, gap="medium")
        for col, module in zip(columns, MODULES[start:start + 3]):
            with col:
                tool_card(module)

    # Aedi AI
    with st.container(key="ai-strip"):
        html("""
        <div class="ai-title">Not sure where to start? Ask Aedi AI.</div>
        <div class="ai-copy">Get help with questions about your plan, in simple words.</div>
        """)
        st.page_link("pages/8_Aedi_AI.py", label="Ask Aedi AI")

    # Suggested path
    html("""
    <div class="section-heading" style="margin-top:44px">A simple way to go through it</div>
    <div class="section-description">Four steps from first idea to a clear picture.</div>
    <div class="path">
        <div class="path-step">
            <div class="path-num">1</div>
            <div class="path-name">Check your plot</div>
            <div class="path-copy">Know how much space you can actually build on.</div>
        </div>
        <div class="path-step">
            <div class="path-num">2</div>
            <div class="path-name">Set your budget</div>
            <div class="path-copy">Estimate the cost, then the materials you will need.</div>
        </div>
        <div class="path-step">
            <div class="path-num">3</div>
            <div class="path-name">Choose a layout</div>
            <div class="path-copy">Compare ideas and check parking and airflow.</div>
        </div>
        <div class="path-step">
            <div class="path-num">4</div>
            <div class="path-name">Review and decide</div>
            <div class="path-copy">Check quotations, then see everything in your summary.</div>
        </div>
    </div>
    """)

    # Disclaimer
    html("""
    <div class="disclaimer">
        <strong>Please note.</strong> AediPueblo gives preliminary estimates and
        planning indicators. It does not replace approved architectural or
        structural plans. Rates and assumptions may differ from your actual site.
        Check local regulations and consult a qualified professional before
        you make construction decisions.
    </div>
    """)

    # Footer
    html("""
    <div class="footer">
        <span>© 2026 AediPueblo</span>
        <span>Designed and developed by <strong>Meena Gayathri S.</strong></span>
        <span>Built with Python and Streamlit</span>
    </div>
    """)


# ---------------------------------------------------------
# NAVIGATION (unchanged)
# ---------------------------------------------------------

# NAVIGATION
pg = st.navigation([
    st.Page(home, title="Home", default=True),
    st.Page("pages/1_Plot_Analysis.py", title="Plot Analysis"),
    st.Page("pages/2_Cost_Estimator.py", title="Cost Estimator"),
    st.Page("pages/3_Materials_Estimator.py", title="Material Estimator"),
    st.Page("pages/5_Layout_Comparison.py", title="Layout Comparison"),
    st.Page("pages/6_Quotation_Checker.py", title="Quotation Checker"),
    st.Page("pages/7_Parking_Ventilation.py", title="Parking and Ventilation"),
    st.Page("pages/8_Aedi_AI.py", title="Aedi AI"),
    st.Page("pages/4_Results_Dashboard.py", title="Results Dashboard"),
])

pg.run()
