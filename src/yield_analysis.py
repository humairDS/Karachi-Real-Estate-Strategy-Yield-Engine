"""Rental yield engine: match sale vs rent asking prices by area, type, and size."""

from __future__ import annotations

import numpy as np
import pandas as pd

VACANCY = 0.08
MAINTENANCE = 0.01
AGENCY_FEE = 0.005


def _size_bucket(sqyd: float) -> str:
    if sqyd < 90:
        return "Compact (<90 sq yd)"
    if sqyd < 160:
        return "Small (90-160)"
    if sqyd < 280:
        return "Medium (160-280)"
    if sqyd < 450:
        return "Large (280-450)"
    return "Estate (450+)"


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["size_bucket"] = out["area_sqyd"].map(_size_bucket)
    out["bed_band"] = pd.cut(
        out["bedrooms"].fillna(0),
        bins=[-0.1, 0, 2, 3, 4, 20],
        labels=["N/A", "1-2", "3", "4", "5+"],
    ).astype(str)
    return out


def area_yield_table(df: pd.DataFrame) -> pd.DataFrame:
    feat = add_features(df)
    keys = ["location_std", "property_type", "size_bucket"]
    sale = (
        feat[feat["purpose"] == "For Sale"]
        .groupby(keys, as_index=False)
        .agg(
            sale_listings=("listing_id", "count"),
            median_sale_pkr=("price_pkr", "median"),
            mean_sale_pkr=("price_pkr", "mean"),
            median_psf=("price_per_sqft", "median"),
            median_sqyd=("area_sqyd", "median"),
        )
    )
    rent = (
        feat[feat["purpose"] == "For Rent"]
        .groupby(keys, as_index=False)
        .agg(
            rent_listings=("listing_id", "count"),
            median_rent_monthly=("price_pkr", "median"),
            mean_rent_monthly=("price_pkr", "mean"),
        )
    )
    merged = sale.merge(rent, on=keys, how="inner")
    merged["annual_rent"] = merged["median_rent_monthly"] * 12
    merged["gross_yield_pct"] = 100 * merged["annual_rent"] / merged["median_sale_pkr"]
    opex = merged["median_sale_pkr"] * (VACANCY + MAINTENANCE + AGENCY_FEE)
    merged["net_yield_pct"] = 100 * (merged["annual_rent"] - opex) / merged["median_sale_pkr"]
    merged["payback_years"] = merged["median_sale_pkr"] / merged["annual_rent"]
    merged["yield_vs_policy"] = merged["gross_yield_pct"] - 11.5
    merged["investment_score"] = (
        0.45 * merged["gross_yield_pct"].clip(0, 15)
        + 0.25 * np.log1p(merged["sale_listings"] + merged["rent_listings"])
        + 0.30 * (merged["rent_listings"] / (merged["sale_listings"] + 1)).clip(0, 3)
    )
    return merged.sort_values("gross_yield_pct", ascending=False)


def location_summary(df: pd.DataFrame, yields: pd.DataFrame) -> pd.DataFrame:
    loc = (
        df.groupby(["location_std", "purpose"], as_index=False)
        .agg(n=("listing_id", "count"), median_price=("price_pkr", "median"), median_psf=("price_per_sqft", "median"))
    )
    wide = loc.pivot(index="location_std", columns="purpose", values=["n", "median_price", "median_psf"])
    wide.columns = ["_".join([str(c) for c in col]).strip() for col in wide.columns]
    wide = wide.reset_index()
    y = (
        yields.groupby("location_std", as_index=False)
        .agg(
            median_gross_yield=("gross_yield_pct", "median"),
            median_net_yield=("net_yield_pct", "median"),
            matched_segments=("property_type", "count"),
        )
    )
    return wide.merge(y, on="location_std", how="left")


def estimate_deal(sale_price: float, monthly_rent: float) -> dict:
    annual = monthly_rent * 12
    gross = 100 * annual / sale_price if sale_price else 0
    net = gross - 100 * (VACANCY + MAINTENANCE + AGENCY_FEE)
    return {
        "annual_rent": annual,
        "gross_yield_pct": gross,
        "net_yield_pct": net,
        "payback_years": sale_price / annual if annual else None,
        "beats_policy_rate": net > 11.5,
    }
