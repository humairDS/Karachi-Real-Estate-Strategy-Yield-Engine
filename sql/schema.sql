-- Karachi real estate star schema (SQLite / Power BI / SQL Server compatible)

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
    furnishing TEXT
);

CREATE TABLE fact_yield (
    yield_id INTEGER PRIMARY KEY,
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
    investment_score REAL
);
