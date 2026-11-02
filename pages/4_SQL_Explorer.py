from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database import SAMPLE_QUERIES, run_query

st.set_page_config(page_title="SQL explorer", layout="wide")
st.title("SQL explorer")
st.caption("SQLite warehouse at `data/sql/karachi_real_estate.db` — same star schema you can open in Power BI.")

choice = st.selectbox("Sample query", list(SAMPLE_QUERIES.keys()))
sql = st.text_area("SQL", SAMPLE_QUERIES[choice].strip(), height=220)

if st.button("Run query", type="primary"):
    try:
        result = run_query(sql)
        st.success(f"{len(result):,} rows")
        st.dataframe(result, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", result.to_csv(index=False), "query_result.csv", "text/csv")
    except Exception as exc:
        st.error(str(exc))

st.markdown(
    """
    **Tables:** `dim_location`, `dim_property_type`, `fact_listings`, `fact_yield`  
    **View:** `v_area_kpis`
    """
)
