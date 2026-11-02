from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CLEAN_LISTINGS_CSV, SQLITE_PATH, YIELD_CSV
from src.eda import overview_kpis
from src.formatters import pkr
from src.pipeline import run

st.set_page_config(
    page_title="Karachi Real Estate & Yield",
    page_icon="🏙",
    layout="wide",
)

st.markdown(
    """
    <style>
    .hero {font-size: 2.1rem; font-weight: 700; margin-bottom: 0.2rem;}
    .sub {color: #C9B8A8; margin-bottom: 1.4rem;}
    div[data-testid="stMetricValue"] {font-size: 1.35rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not CLEAN_LISTINGS_CSV.exists() or not YIELD_CSV.exists() or not SQLITE_PATH.exists():
        run(regenerate_raw=True)
    listings = pd.read_csv(CLEAN_LISTINGS_CSV, parse_dates=["listing_dt"])
    yields = pd.read_csv(YIELD_CSV)
    return listings, yields


with st.sidebar:
    st.header("Pipeline")
    st.caption("Raw portal-style CSVs → clean tables → SQLite → yield model.")
    if st.button("Rebuild data warehouse", type="primary"):
        st.cache_data.clear()
        info = run(regenerate_raw=True)
        st.success(f"Loaded {info['clean_rows']} clean rows from {info['raw_rows']} raw listings.")
    st.markdown("---")
    st.markdown(
        "Swap `data/raw/*.csv` with your own Zameen/Graana export, then rebuild. "
        "Column aliases are in `src/ingest.py`."
    )

listings, yields = load_tables()
kpis = overview_kpis(listings)

st.markdown('<div class="hero">Karachi Real Estate & Yield Lab</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Asking-price analytics for sale vs rent, neighbourhood yield, SQL warehouse, and Power BI extracts.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Clean listings", f"{kpis['listings']:,}")
c2.metric("For sale", f"{kpis['sale']:,}")
c3.metric("For rent", f"{kpis['rent']:,}")
c4.metric("Median sale", pkr(kpis["median_sale_crore"] * 10_000_000))
c5.metric("Median monthly rent", pkr(kpis["median_rent"]))

st.info(
    "Figures are **asking prices** modelled on 2025–2026 Karachi portal bands "
    "(DHA, Clifton, Bahria, Gulshan, Jauhar, and others). They are not registered sale deeds. "
    "Citywide reported residential yields sit around 4–8% for homes and higher for commercial corridors."
)

left, right = st.columns((1.15, 1))
sale = listings[listings["purpose"] == "For Sale"]
loc_med = (
    sale.groupby("location_std", as_index=False)
    .agg(median_crore=("price_crore", "median"), n=("listing_id", "count"), median_psf=("price_per_sqft", "median"))
    .sort_values("median_crore", ascending=False)
)
fig = px.bar(
    loc_med,
    x="median_crore",
    y="location_std",
    orientation="h",
    color="median_psf",
    labels={"median_crore": "Median asking (crore PKR)", "location_std": "Area", "median_psf": "PKR / sq ft"},
    title="Median sale asking price by area",
)
fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=560, paper_bgcolor="rgba(0,0,0,0)")
left.plotly_chart(fig, use_container_width=True)

y_loc = (
    yields.groupby("location_std", as_index=False)["gross_yield_pct"]
    .median()
    .sort_values("gross_yield_pct", ascending=False)
)
fig2 = px.bar(
    y_loc,
    x="gross_yield_pct",
    y="location_std",
    orientation="h",
    title="Median gross rental yield by area",
    labels={"gross_yield_pct": "Gross yield %", "location_std": "Area"},
    color="gross_yield_pct",
    color_continuous_scale="YlOrRd",
)
fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=560, paper_bgcolor="rgba(0,0,0,0)")
right.plotly_chart(fig2, use_container_width=True)

st.subheader("How this project is wired")
a, b, c = st.columns(3)
a.markdown(
    "**1. Extract**\n\n`data/raw/` holds Zameen-style sale and rent CSVs "
    "(messy prices, mixed units, duplicate IDs). Replace them with portal exports anytime."
)
b.markdown(
    "**2. Clean + SQL**\n\n`src/clean.py` standardises PKR, sq yd, locations. "
    "`src/database.py` loads a star schema into SQLite for SQL practice and Power BI."
)
c.markdown(
    "**3. Yield + Streamlit**\n\nGross yield = 12 × median rent / median sale, matched on area, type, and size. "
    "Use the sidebar pages for EDA, deal calculator, and SQL."
)
