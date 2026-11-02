"""Clean messy Karachi listing CSVs into analysis-ready tables."""

from __future__ import annotations

import re
from datetime import datetime

import numpy as np
import pandas as pd

from src.generate_sample_data import AREAS

LOCATION_MAP = {}
for area in AREAS:
    LOCATION_MAP[area["name"].lower()] = area["name"]
    for alias in area["aliases"]:
        LOCATION_MAP[alias.lower()] = area["name"]

TYPE_MAP = {
    "house": "House",
    "bungalow": "House",
    "flat": "Flat",
    "apartment": "Flat",
    "appartment": "Flat",
    "plot": "Plot",
    "penthouse": "Penthouse",
    "commercial": "Commercial",
    "shop": "Commercial",
    "office": "Commercial",
    "upper portion": "Upper Portion",
    "lower portion": "Lower Portion",
}

PURPOSE_MAP = {
    "for sale": "For Sale",
    "sale": "For Sale",
    "buy": "For Sale",
    "for rent": "For Rent",
    "rent": "For Rent",
    "rental": "For Rent",
}


def parse_price(value) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip().lower().replace(",", "")
    if text in {"", "n/a", "na", "-", "call for price", "price on request"}:
        return None
    text = text.replace("pkr", "").replace("rs.", "").replace("rs", "").strip()
    crore = re.search(r"([0-9]*\.?[0-9]+)\s*(crore|cr)\b", text)
    if crore:
        return float(crore.group(1)) * 10_000_000
    lac = re.search(r"([0-9]*\.?[0-9]+)\s*(lac|lakh|lacs)\b", text)
    if lac:
        return float(lac.group(1)) * 100_000
    num = re.search(r"([0-9]*\.?[0-9]+)", text)
    if not num:
        return None
    amount = float(num.group(1))
    return amount if amount > 0 else None


def parse_area_to_sqyd(area, unit) -> float | None:
    try:
        size = float(str(area).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    if size <= 0:
        return None
    u = str(unit or "").strip().lower()
    if "marla" in u:
        return size * 30.25
    if "kanal" in u:
        return size * 605
    if "ft" in u or "feet" in u or "sqft" in u or "sq. ft" in u:
        return size / 9.0
    if "m2" in u or "sqm" in u or "meter" in u:
        return size / 0.836127
    return size  # default sq yards / gazz


def parse_date(value) -> datetime | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d %b %Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return pd.to_datetime(text, dayfirst=True, errors="coerce")


def canonical_location(value: str) -> str:
    key = re.sub(r"\s+", " ", str(value).strip().lower())
    if key in LOCATION_MAP:
        return LOCATION_MAP[key]
    for alias, name in LOCATION_MAP.items():
        if alias in key or key in alias:
            return name
    return str(value).strip().title() or "Unknown"


def clean_listings(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    for col in [
        "property_id", "title", "purpose", "property_type", "city", "location",
        "area", "area_unit", "bedrooms", "bathrooms", "price", "latitude",
        "longitude", "agency", "agent", "listing_date", "year_built",
        "parking", "furnishing", "source", "description",
    ]:
        if col not in df.columns:
            df[col] = ""

    df["price_pkr"] = df["price"].map(parse_price)
    df["area_sqyd"] = [
        parse_area_to_sqyd(a, u) for a, u in zip(df["area"], df["area_unit"])
    ]
    df["area_sqft"] = df["area_sqyd"] * 9.0
    df["purpose"] = df["purpose"].astype(str).str.strip().str.lower().map(PURPOSE_MAP).fillna("Unknown")
    df["property_type"] = (
        df["property_type"].astype(str).str.strip().str.lower().map(TYPE_MAP).fillna("Other")
    )
    df["location_std"] = df["location"].map(canonical_location)
    df["city"] = "Karachi"
    df["source"] = df["source"].astype(str).str.strip().str.title().replace({"Zameen": "Zameen.com"})
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["year_built"] = pd.to_numeric(df["year_built"], errors="coerce")
    df["listing_dt"] = df["listing_date"].map(parse_date)
    df["listing_dt"] = pd.to_datetime(df["listing_dt"], errors="coerce")
    df["agency"] = df["agency"].replace({"": "Unknown", "N/A": "Unknown"}).fillna("Unknown")
    furn = df["furnishing"].astype(str).str.strip().str.lower()
    df["furnishing"] = furn.map({
        "unfurnished": "Unfurnished",
        "un furnished": "Unfurnished",
        "semi-furnished": "Semi-Furnished",
        "semi furnished": "Semi-Furnished",
        "furnished": "Furnished",
    }).fillna("Unknown")

    df = df.dropna(subset=["price_pkr", "area_sqyd"])
    df = df[df["price_pkr"] > 0]
    df = df[df["area_sqyd"].between(20, 5000)]

    df["price_per_sqyd"] = df["price_pkr"] / df["area_sqyd"]
    df["price_per_sqft"] = df["price_pkr"] / df["area_sqft"]
    sale_mask = df["purpose"] == "For Sale"
    rent_mask = df["purpose"] == "For Rent"

    # Drop extreme asking-price outliers within location + type (sale vs rent separately)
    cleaned_parts = []
    for mask in (sale_mask, rent_mask, ~(sale_mask | rent_mask)):
        part = df[mask]
        if part.empty:
            continue
        part = part.copy()
        grp = part.groupby(["location_std", "property_type"])["price_pkr"]
        q1 = grp.transform(lambda s: s.quantile(0.01) if len(s) > 8 else s.min())
        q99 = grp.transform(lambda s: s.quantile(0.99) if len(s) > 8 else s.max())
        part = part[(part["price_pkr"] >= q1) & (part["price_pkr"] <= q99)]
        cleaned_parts.append(part)
    df = pd.concat(cleaned_parts, ignore_index=True) if cleaned_parts else df.iloc[0:0]

    df = df.sort_values("listing_dt", na_position="last")
    df = df.drop_duplicates(subset=["property_id", "purpose"], keep="last")
    df = df.reset_index(drop=True)
    df["listing_id"] = np.arange(1, len(df) + 1)
    df["price_crore"] = df["price_pkr"] / 10_000_000
    df["price_lac"] = df["price_pkr"] / 100_000
    df["monthly_rent_pkr"] = np.where(df["purpose"] == "For Rent", df["price_pkr"], np.nan)
    df["sale_price_pkr"] = np.where(df["purpose"] == "For Sale", df["price_pkr"], np.nan)
    return df


def quality_report(raw: pd.DataFrame, clean: pd.DataFrame) -> dict:
    return {
        "raw_rows": int(len(raw)),
        "clean_rows": int(len(clean)),
        "dropped": int(len(raw) - len(clean)),
        "sale_rows": int((clean["purpose"] == "For Sale").sum()),
        "rent_rows": int((clean["purpose"] == "For Rent").sum()),
        "locations": int(clean["location_std"].nunique()),
        "missing_price_raw": int(raw["price"].astype(str).str.lower().isin(["", "n/a", "na", "-", "call for price"]).sum()) if "price" in raw.columns else 0,
        "duplicates_removed": max(0, int(len(raw) - len(clean))),
    }
