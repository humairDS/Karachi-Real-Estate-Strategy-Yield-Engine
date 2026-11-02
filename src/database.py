"""SQLite warehouse for listings, yields, and Power BI extracts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from config import SQLITE_PATH

SCHEMA_SQL = """
DROP VIEW IF EXISTS v_area_kpis;
DROP TABLE IF EXISTS fact_listings;
DROP TABLE IF EXISTS fact_yield;
DROP TABLE IF EXISTS dim_location;
DROP TABLE IF EXISTS dim_property_type;

CREATE TABLE dim_location (
    location_id INTEGER PRIMARY KEY,
    location_name TEXT UNIQUE NOT NULL,
    city TEXT DEFAULT 'Karachi'
);

CREATE TABLE dim_property_type (
    type_id INTEGER PRIMARY KEY,
    property_type TEXT UNIQUE NOT NULL
);

CREATE TABLE fact_listings (
    listing_id INTEGER PRIMARY KEY,
    property_id TEXT,
    purpose TEXT,
    location_id INTEGER,
    type_id INTEGER,
    area_sqyd REAL,
    area_sqft REAL,
    bedrooms REAL,
    bathrooms REAL,
    price_pkr REAL,
    price_per_sqft REAL,
    latitude REAL,
    longitude REAL,
    agency TEXT,
    source TEXT,
    listing_date TEXT,
    year_built REAL,
    furnishing TEXT,
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (type_id) REFERENCES dim_property_type(type_id)
);

CREATE TABLE fact_yield (
    yield_id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER,
    type_id INTEGER,
    size_bucket TEXT,
    sale_listings INTEGER,
    rent_listings INTEGER,
    median_sale_pkr REAL,
    median_rent_monthly REAL,
    gross_yield_pct REAL,
    net_yield_pct REAL,
    payback_years REAL,
    investment_score REAL,
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (type_id) REFERENCES dim_property_type(type_id)
);

CREATE VIEW v_area_kpis AS
SELECT
    l.location_name,
    t.property_type,
    COUNT(*) AS listings,
    AVG(CASE WHEN f.purpose = 'For Sale' THEN f.price_pkr END) AS avg_sale,
    AVG(CASE WHEN f.purpose = 'For Rent' THEN f.price_pkr END) AS avg_rent,
    AVG(f.price_per_sqft) AS avg_psf
FROM fact_listings f
JOIN dim_location l ON l.location_id = f.location_id
JOIN dim_property_type t ON t.type_id = f.type_id
GROUP BY l.location_name, t.property_type;
"""


def engine(path: Path = SQLITE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}")


def load_warehouse(clean: pd.DataFrame, yields: pd.DataFrame, path: Path = SQLITE_PATH) -> None:
    eng = engine(path)
    with eng.begin() as conn:
        for stmt in SCHEMA_SQL.split(";"):
            s = stmt.strip()
            if s:
                conn.execute(text(s))

    locations = pd.DataFrame({"location_name": sorted(clean["location_std"].dropna().unique())})
    locations["location_id"] = range(1, len(locations) + 1)
    types = pd.DataFrame({"property_type": sorted(clean["property_type"].dropna().unique())})
    types["type_id"] = range(1, len(types) + 1)

    loc_map = dict(zip(locations["location_name"], locations["location_id"]))
    type_map = dict(zip(types["property_type"], types["type_id"]))

    facts = pd.DataFrame({
        "listing_id": clean["listing_id"],
        "property_id": clean["property_id"],
        "purpose": clean["purpose"],
        "location_id": clean["location_std"].map(loc_map),
        "type_id": clean["property_type"].map(type_map),
        "area_sqyd": clean["area_sqyd"],
        "area_sqft": clean["area_sqft"],
        "bedrooms": clean["bedrooms"],
        "bathrooms": clean["bathrooms"],
        "price_pkr": clean["price_pkr"],
        "price_per_sqft": clean["price_per_sqft"],
        "latitude": clean["latitude"],
        "longitude": clean["longitude"],
        "agency": clean["agency"],
        "source": clean["source"],
        "listing_date": clean["listing_dt"].astype(str),
        "year_built": clean["year_built"],
        "furnishing": clean["furnishing"],
    })

    y = yields.copy()
    y["location_id"] = y["location_std"].map(loc_map)
    y["type_id"] = y["property_type"].map(type_map)
    y = y.dropna(subset=["location_id", "type_id"])
    y_out = y[[
        "location_id", "type_id", "size_bucket", "sale_listings", "rent_listings",
        "median_sale_pkr", "median_rent_monthly", "gross_yield_pct", "net_yield_pct",
        "payback_years", "investment_score",
    ]]

    locations.to_sql("dim_location", eng, if_exists="append", index=False)
    types.to_sql("dim_property_type", eng, if_exists="append", index=False)
    facts.to_sql("fact_listings", eng, if_exists="append", index=False)
    y_out.to_sql("fact_yield", eng, if_exists="append", index=False)


def run_query(sql: str, path: Path = SQLITE_PATH) -> pd.DataFrame:
    eng = engine(path)
    return pd.read_sql(text(sql), eng)


SAMPLE_QUERIES = {
    "Top yields": """
        SELECT l.location_name, t.property_type, y.size_bucket,
               ROUND(y.gross_yield_pct, 2) AS gross_yield,
               ROUND(y.net_yield_pct, 2) AS net_yield,
               y.sale_listings, y.rent_listings
        FROM fact_yield y
        JOIN dim_location l ON l.location_id = y.location_id
        JOIN dim_property_type t ON t.type_id = y.type_id
        ORDER BY y.gross_yield_pct DESC
        LIMIT 20;
    """,
    "Median sale by location": """
        SELECT l.location_name,
               COUNT(*) AS n,
               ROUND(AVG(f.price_pkr)/10000000.0, 2) AS avg_crore,
               ROUND(AVG(f.price_per_sqft), 0) AS avg_psf
        FROM fact_listings f
        JOIN dim_location l ON l.location_id = f.location_id
        WHERE f.purpose = 'For Sale'
        GROUP BY l.location_name
        ORDER BY avg_crore DESC;
    """,
    "Inventory mix": """
        SELECT t.property_type, f.purpose, COUNT(*) AS listings
        FROM fact_listings f
        JOIN dim_property_type t ON t.type_id = f.type_id
        GROUP BY t.property_type, f.purpose
        ORDER BY listings DESC;
    """,
}
