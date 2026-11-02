from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import YIELD_CSV
from src.formatters import pkr
from src.yield_analysis import estimate_deal

st.set_page_config(page_title="Yield analyzer", layout="wide")
st.title("Rental yield analyzer")
st.caption("Gross yield = 12 × median monthly rent ÷ median sale asking price, matched on area, type, and size bucket.")

yd = pd.read_csv(YIELD_CSV)

c1, c2, c3 = st.columns(3)
c1.metric("Matched segments", f"{len(yd):,}")
c2.metric("Median gross yield", f"{yd['gross_yield_pct'].median():.2f}%")
c3.metric("Median net yield", f"{yd['net_yield_pct'].median():.2f}%")

st.markdown(
    "Net yield subtracts an 8% vacancy, 1% maintenance, and 0.5% agency allowance. "
    "SBP policy rate context used in the model is **11.5%** (mid-2026)."
)

heat = yd.pivot_table(index="location_std", columns="property_type", values="gross_yield_pct", aggfunc="median")
fig = px.imshow(
    heat,
    aspect="auto",
    color_continuous_scale="YlOrRd",
    title="Gross yield heatmap (area × type)",
    labels={"color": "Gross %"},
)
fig.update_layout(height=520, paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Top investment segments")
top = yd.sort_values("investment_score", ascending=False).head(25)
st.dataframe(
    top.assign(
        median_sale=lambda d: d["median_sale_pkr"].map(lambda x: pkr(x, 2)),
        median_rent=lambda d: d["median_rent_monthly"].map(lambda x: pkr(x)),
        gross=lambda d: d["gross_yield_pct"].round(2),
        net=lambda d: d["net_yield_pct"].round(2),
    )[
        ["location_std", "property_type", "size_bucket", "sale_listings", "rent_listings", "median_sale", "median_rent", "gross", "net", "payback_years", "investment_score"]
    ],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Deal calculator")
d1, d2, d3 = st.columns(3)
sale = d1.number_input("Purchase / asking price (PKR)", min_value=1_000_000.0, value=25_000_000.0, step=500_000.0)
rent = d2.number_input("Expected monthly rent (PKR)", min_value=10_000.0, value=120_000.0, step=5_000.0)
est = estimate_deal(sale, rent)
d3.metric("Gross yield", f"{est['gross_yield_pct']:.2f}%")
e1, e2, e3 = st.columns(3)
e1.metric("Net yield", f"{est['net_yield_pct']:.2f}%")
e2.metric("Payback", f"{est['payback_years']:.1f} years" if est["payback_years"] else "—")
e3.metric("Beats 11.5% policy rate (net)?", "Yes" if est["beats_policy_rate"] else "No")

fig2 = px.scatter(
    yd,
    x="median_sale_pkr",
    y="gross_yield_pct",
    color="property_type",
    size="rent_listings",
    hover_name="location_std",
    title="Sale price vs gross yield",
    labels={"median_sale_pkr": "Median sale (PKR)", "gross_yield_pct": "Gross yield %"},
)
fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig2, use_container_width=True)
