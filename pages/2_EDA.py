from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CLEAN_LISTINGS_CSV
from src.eda import location_price_table, numeric_describe, type_breakdown

st.set_page_config(page_title="EDA", layout="wide")
st.title("Exploratory analysis")

df = pd.read_csv(CLEAN_LISTINGS_CSV, parse_dates=["listing_dt"])

areas = ["All"] + sorted(df["location_std"].unique())
types = ["All"] + sorted(df["property_type"].unique())
purposes = ["All", "For Sale", "For Rent"]

f1, f2, f3 = st.columns(3)
area = f1.selectbox("Area", areas)
ptype = f2.selectbox("Property type", types)
purpose = f3.selectbox("Purpose", purposes)

view = df.copy()
if area != "All":
    view = view[view["location_std"] == area]
if ptype != "All":
    view = view[view["property_type"] == ptype]
if purpose != "All":
    view = view[view["purpose"] == purpose]

st.caption(f"{len(view):,} listings in the current filter.")

c1, c2 = st.columns(2)
fig = px.histogram(view, x="price_pkr", nbins=40, color="purpose", title="Price distribution (PKR)")
fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
c1.plotly_chart(fig, use_container_width=True)

fig2 = px.box(
    view[view["purpose"] == "For Sale"] if purpose != "For Rent" else view,
    x="property_type",
    y="price_per_sqft",
    title="PKR per sq ft by type",
)
fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
c2.plotly_chart(fig2, use_container_width=True)

map_df = view.dropna(subset=["latitude", "longitude"])
if not map_df.empty:
    figm = px.scatter_mapbox(
        map_df.sample(min(len(map_df), 800), random_state=1),
        lat="latitude",
        lon="longitude",
        color="purpose",
        size="area_sqyd",
        hover_name="location_std",
        hover_data={"price_pkr": ":.0f", "property_type": True, "area_sqyd": ":.0f"},
        zoom=9.4,
        height=480,
        title="Listing map (sample)",
    )
    figm.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(figm, use_container_width=True)

st.subheader("By property type")
st.dataframe(type_breakdown(view), use_container_width=True, hide_index=True)

st.subheader("Sale asking prices by neighbourhood")
st.dataframe(location_price_table(view if purpose != "For Rent" else df), use_container_width=True, hide_index=True)

st.subheader("Numeric summary")
st.dataframe(numeric_describe(view), use_container_width=True)

if view["listing_dt"].notna().any():
    ts = (
        view.dropna(subset=["listing_dt"])
        .assign(month=lambda d: d["listing_dt"].dt.to_period("M").dt.to_timestamp())
        .groupby(["month", "purpose"], as_index=False)
        .size()
    )
    figt = px.line(ts, x="month", y="size", color="purpose", title="Listing volume by month")
    figt.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(figt, use_container_width=True)
