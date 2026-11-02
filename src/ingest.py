"""Load portal CSVs (Zameen / Graana / OLX exports) into a common schema."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

COLUMN_ALIASES = {
    "property_id": ["property_id", "id", "listing_id", "propertyid"],
    "title": ["title", "heading", "name"],
    "purpose": ["purpose", "type_of_listing", "listing_type"],
    "property_type": ["property_type", "type", "category", "propertytype"],
    "city": ["city"],
    "location": ["location", "locality", "area_name", "neighbourhood", "neighborhood", "address"],
    "area": ["area", "area_size", "size", "covered_area"],
    "area_unit": ["area_unit", "unit", "size_unit"],
    "bedrooms": ["bedrooms", "beds", "bed"],
    "bathrooms": ["bathrooms", "baths", "bath"],
    "price": ["price", "asking_price", "amount"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng"],
    "agency": ["agency", "agency_name", "company"],
    "agent": ["agent", "agent_name", "contact_person"],
    "listing_date": ["listing_date", "date", "posted_on", "added"],
    "year_built": ["year_built", "built_year", "construction_year"],
    "parking": ["parking", "car_parking"],
    "furnishing": ["furnishing", "furnished"],
    "source": ["source", "portal", "website"],
    "description": ["description", "details", "remarks"],
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {c: c.strip().lower().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=mapping)
    rename = {}
    used = set()
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in df.columns and canonical not in used:
                rename[alias] = canonical
                used.add(canonical)
                break
    return df.rename(columns=rename)


def load_raw_csv(path: Path, default_purpose: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df = _normalize_columns(df)
    if "purpose" not in df.columns and default_purpose:
        df["purpose"] = default_purpose
    if "source" not in df.columns:
        df["source"] = path.stem
    df["raw_file"] = path.name
    return df


def load_all_raw(paths: list[Path], purposes: list[str | None] | None = None) -> pd.DataFrame:
    frames = []
    purposes = purposes or [None] * len(paths)
    for path, purpose in zip(paths, purposes):
        if path.exists():
            frames.append(load_raw_csv(path, purpose))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
