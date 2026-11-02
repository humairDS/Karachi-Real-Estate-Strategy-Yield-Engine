from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CLEAN_LISTINGS_CSV, RAW_RENT_CSV, RAW_SALE_CSV
from src.clean import quality_report
from src.ingest import load_all_raw

st.set_page_config(page_title="Data pipeline", layout="wide")
st.title("Data pipeline")
st.caption("Raw portal CSVs compared with the cleaned warehouse table.")

raw = load_all_raw([RAW_SALE_CSV, RAW_RENT_CSV], ["For Sale", "For Rent"])
clean = pd.read_csv(CLEAN_LISTINGS_CSV)
report = quality_report(raw, clean)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Raw rows", f"{report['raw_rows']:,}")
k2.metric("Clean rows", f"{report['clean_rows']:,}")
k3.metric("Dropped / invalid", f"{report['dropped']:,}")
k4.metric("Neighbourhoods", report["locations"])

st.subheader("Cleaning rules")
st.markdown(
    """
    - Parse prices in `Crore`, `Lac`, `PKR`, commas, and drop `Call for price`
    - Convert Marla / sq ft / sq yd to a single **sq yd** and **sq ft**
    - Canonicalise locations (`Gulshan e Iqbal` → `Gulshan-e-Iqbal`)
    - Standardise purpose and property type
    - Remove 1st/99th percentile outliers within area + type
    - Deduplicate `property_id` + purpose
    """
)

left, right = st.columns(2)
left.subheader("Raw sample")
left.dataframe(raw.head(25), use_container_width=True, hide_index=True)
right.subheader("Clean sample")
show = clean[
    ["listing_id", "purpose", "property_type", "location_std", "area_sqyd", "bedrooms", "price_pkr", "price_per_sqft", "source"]
].head(25)
right.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("Bring your own Zameen CSV")
st.markdown(
    "Export listings from a portal, save as CSV in `data/raw/`, keep a `price`, `location`, `area`, and `purpose` column "
    "(other headings are aliased), then click **Rebuild data warehouse** on the home page."
)
uploaded = st.file_uploader("Preview an export", type=["csv"])
if uploaded:
    preview = pd.read_csv(uploaded, nrows=30)
    st.dataframe(preview, use_container_width=True)
