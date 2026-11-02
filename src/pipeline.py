"""Run extract → clean → yield → SQLite → Power BI export."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (
    CLEAN_LISTINGS_CSV,
    FEATURE_CSV,
    POWERBI_DIR,
    PROCESSED_DIR,
    RAW_RENT_CSV,
    RAW_SALE_CSV,
    SQLITE_PATH,
    YIELD_CSV,
)
from src.clean import clean_listings, quality_report
from src.database import load_warehouse
from src.generate_sample_data import write_raw
from src.ingest import load_all_raw
from src.yield_analysis import add_features, area_yield_table


def run(regenerate_raw: bool = False) -> dict:
    if regenerate_raw or not RAW_SALE_CSV.exists() or not RAW_RENT_CSV.exists():
        write_raw()

    raw = load_all_raw(
        [RAW_SALE_CSV, RAW_RENT_CSV],
        ["For Sale", "For Rent"],
    )
    clean = clean_listings(raw)
    features = add_features(clean)
    yields = area_yield_table(features)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    POWERBI_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(CLEAN_LISTINGS_CSV, index=False)
    features.to_csv(FEATURE_CSV, index=False)
    yields.to_csv(YIELD_CSV, index=False)

    load_warehouse(clean, yields, SQLITE_PATH)

    sale = clean[clean["purpose"] == "For Sale"][
        ["listing_id", "location_std", "property_type", "area_sqyd", "bedrooms", "price_pkr", "price_per_sqft", "listing_dt"]
    ]
    rent = clean[clean["purpose"] == "For Rent"][
        ["listing_id", "location_std", "property_type", "area_sqyd", "bedrooms", "price_pkr", "listing_dt"]
    ]
    sale.to_csv(POWERBI_DIR / "fact_sale.csv", index=False)
    rent.to_csv(POWERBI_DIR / "fact_rent.csv", index=False)
    yields.to_csv(POWERBI_DIR / "fact_yield.csv", index=False)

    report = quality_report(raw, clean)
    report["yield_segments"] = int(len(yields))
    report["sqlite"] = str(SQLITE_PATH)
    return report


if __name__ == "__main__":
    regen = "--regen" in sys.argv
    info = run(regenerate_raw=regen)
    print(info)
