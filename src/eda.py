"""Reusable EDA summaries for Streamlit and notebooks."""

from __future__ import annotations

import pandas as pd


def overview_kpis(df: pd.DataFrame) -> dict:
    sale = df[df["purpose"] == "For Sale"]
    rent = df[df["purpose"] == "For Rent"]
    return {
        "listings": len(df),
        "sale": len(sale),
        "rent": len(rent),
        "areas": df["location_std"].nunique(),
        "median_sale_crore": sale["price_pkr"].median() / 10_000_000 if len(sale) else 0,
        "median_rent": rent["price_pkr"].median() if len(rent) else 0,
        "median_sale_psf": sale["price_per_sqft"].median() if len(sale) else 0,
        "sources": ", ".join(sorted(df["source"].dropna().unique())),
    }


def type_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["property_type", "purpose"], as_index=False)
        .agg(n=("listing_id", "count"), median_price=("price_pkr", "median"), median_psf=("price_per_sqft", "median"))
        .sort_values("n", ascending=False)
    )


def location_price_table(df: pd.DataFrame) -> pd.DataFrame:
    sale = df[df["purpose"] == "For Sale"]
    return (
        sale.groupby("location_std", as_index=False)
        .agg(
            listings=("listing_id", "count"),
            median_crore=("price_crore", "median"),
            p25_crore=("price_crore", lambda s: s.quantile(0.25)),
            p75_crore=("price_crore", lambda s: s.quantile(0.75)),
            median_psf=("price_per_sqft", "median"),
            median_sqyd=("area_sqyd", "median"),
        )
        .sort_values("median_crore", ascending=False)
    )


def numeric_describe(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["price_pkr", "area_sqyd", "area_sqft", "bedrooms", "bathrooms", "price_per_sqft", "year_built"]
    cols = [c for c in cols if c in df.columns]
    return df[cols].describe().T
