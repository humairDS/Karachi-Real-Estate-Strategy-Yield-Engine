from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SQL_DIR = DATA_DIR / "sql"
POWERBI_DIR = ROOT / "powerbi" / "exports"

RAW_SALE_CSV = RAW_DIR / "zameen_karachi_sale_raw.csv"
RAW_RENT_CSV = RAW_DIR / "zameen_karachi_rent_raw.csv"
CLEAN_LISTINGS_CSV = PROCESSED_DIR / "listings_clean.csv"
YIELD_CSV = PROCESSED_DIR / "area_yield_summary.csv"
FEATURE_CSV = PROCESSED_DIR / "investment_features.csv"
SQLITE_PATH = SQL_DIR / "karachi_real_estate.db"

CITY = "Karachi"
RANDOM_SEED = 42

# Typical Karachi asking-price bands (PKR) used for synthetic Zameen-style data.
# Grounded in 2025–2026 public index / brokerage ranges, not closed deals.
SQFT_PER_SQYD = 9.0
