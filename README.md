# Karachi Real Estate & Yield Lab

Streamlit app for Karachi sale/rent asking prices, neighbourhood yield, SQLite, and Power BI extracts.

## Why the CSVs are generated

Zameen and similar portals block bulk scrapers and terms of use do not allow harvesting full listing dumps. The pipeline ships **Zameen-shaped raw CSVs** (messy prices, mixed units, duplicate IDs) calibrated to 2025–2026 public Karachi bands (DHA, Clifton, Bahria, Gulshan, Jauhar, etc.). Drop your own portal export into `data/raw/` at any time.

## Stack

- Python (pandas, Plotly)
- Streamlit dashboard
- SQLite star schema
- Power BI CSV + DAX kit

## Setup

```powershell
cd C:\Users\UmairPC\karachi-real-estate
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.pipeline --regen
streamlit run app.py
```

## Project layout

```
data/raw/            messy sale + rent CSVs
data/processed/      clean listings + yield tables
data/sql/            SQLite warehouse
src/                 ingest, clean, EDA, yield, pipeline
sql/                 schema + practice queries
powerbi/             DAX measures and CSV exports
pages/               Streamlit multi-page app
```

## Yield formula

Gross yield % = (median monthly rent × 12) / median sale asking price  
Matched on area + property type + size bucket.  
Net yield subtracts 8% vacancy + 1% maintenance + 0.5% agency.

These are **asking-price yields**, not closed-deal IRRs.
