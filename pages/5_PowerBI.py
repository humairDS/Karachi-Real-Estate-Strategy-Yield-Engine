from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "powerbi" / "exports"

st.set_page_config(page_title="Power BI", layout="wide")
st.title("Power BI handoff")
st.markdown(
    """
    This Python project is the **source of truth**. Power BI is the BI layer.

    1. Run `python -m src.pipeline` (or rebuild from the home page)
    2. In Power BI Desktop, **Get data → Text/CSV** and load files in `powerbi/exports/`
    3. Paste measures from `powerbi/dax_measures.dax`
    4. Or use **ODBC → SQLite** against `data/sql/karachi_real_estate.db`
    """
)

if EXPORTS.exists():
    files = list(EXPORTS.glob("*.csv"))
    st.subheader("Export files")
    for f in files:
        st.write(f"- `{f.name}` ({f.stat().st_size / 1024:.1f} KB)")
        data = f.read_bytes()
        st.download_button(f"Download {f.name}", data, file_name=f.name, mime="text/csv", key=f.name)
else:
    st.warning("No exports yet. Rebuild the warehouse from the home page.")

st.subheader("Suggested DAX")
st.code((ROOT / "powerbi" / "dax_measures.dax").read_text(encoding="utf-8"), language="dax")
