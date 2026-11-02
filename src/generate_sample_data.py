"""Generate messy Zameen-style Karachi sale and rent CSVs.

Live portal scraping is blocked, rate-limited, and legally restricted.
This module produces realistic *asking-price* listings so the rest of the
pipeline (clean → SQL → yield → Streamlit → Power BI) can run end to end.

Replace the files in data/raw/ with your own portal exports; column aliases
in src/ingest.py map common Zameen / Graana headings automatically.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import RAW_DIR, RAW_RENT_CSV, RAW_SALE_CSV, RANDOM_SEED

AREAS = [
    {"name": "DHA Phase 6", "aliases": ["DHA Phs 6", "DHA Phase-6", "Defence Phase 6"], "lat": 24.805, "lon": 67.068, "tier": "prime", "plot_120_cr": (2.5, 3.5), "flat_psf": 30000, "house_psf": 28000, "yield": 0.048},
    {"name": "DHA Phase 8", "aliases": ["DHA Ph-8", "DHA Phase8", "Defence Phase 8"], "lat": 24.822, "lon": 67.082, "tier": "prime", "plot_120_cr": (1.8, 2.8), "flat_psf": 26000, "house_psf": 24000, "yield": 0.052},
    {"name": "DHA Phase 5", "aliases": ["DHA Ph 5", "Defence Phase 5"], "lat": 24.814, "lon": 67.055, "tier": "prime", "plot_120_cr": (2.8, 4.0), "flat_psf": 32000, "house_psf": 30000, "yield": 0.045},
    {"name": "DHA Phase 4", "aliases": ["DHA Ph-4"], "lat": 24.821, "lon": 67.048, "tier": "prime", "plot_120_cr": (3.0, 4.2), "flat_psf": 31000, "house_psf": 29000, "yield": 0.044},
    {"name": "DHA Phase 2", "aliases": ["DHA II"], "lat": 24.832, "lon": 67.052, "tier": "prime", "plot_120_cr": (3.2, 4.5), "flat_psf": 33000, "house_psf": 31000, "yield": 0.042},
    {"name": "Clifton", "aliases": ["Clifton Block 2", "Clifton Karachi", "clifton"], "lat": 24.813, "lon": 67.028, "tier": "prime", "plot_120_cr": (4.0, 7.0), "flat_psf": 25000, "house_psf": 27000, "yield": 0.05},
    {"name": "Bath Island", "aliases": ["BathIsland"], "lat": 24.821, "lon": 67.031, "tier": "prime", "plot_120_cr": (5.0, 8.0), "flat_psf": 35000, "house_psf": 32000, "yield": 0.046},
    {"name": "PECHS", "aliases": ["P.E.C.H.S", "Pechs Block 6"], "lat": 24.874, "lon": 67.058, "tier": "mid", "plot_120_cr": (1.8, 3.0), "flat_psf": 18000, "house_psf": 22000, "yield": 0.062},
    {"name": "Gulshan-e-Iqbal", "aliases": ["Gulshan e Iqbal", "Gulshan Iqbal", "gulshan-e-iqbal town"], "lat": 24.917, "lon": 67.092, "tier": "mid", "plot_120_cr": (1.2, 1.8), "flat_psf": 16000, "house_psf": 20000, "yield": 0.068},
    {"name": "Gulistan-e-Jauhar", "aliases": ["Gulistan e Jauhar", "Jauhar", "Gulistan-e-Johar"], "lat": 24.907, "lon": 67.135, "tier": "mid", "plot_120_cr": (0.9, 1.5), "flat_psf": 12000, "house_psf": 16000, "yield": 0.072},
    {"name": "North Nazimabad", "aliases": ["N. Nazimabad", "North nazimabad"], "lat": 24.937, "lon": 67.038, "tier": "mid", "plot_120_cr": (0.8, 1.3), "flat_psf": 15000, "house_psf": 18000, "yield": 0.065},
    {"name": "Federal B Area", "aliases": ["F.B Area", "FB Area", "Federal B. Area"], "lat": 24.933, "lon": 67.072, "tier": "mid", "plot_120_cr": (0.85, 1.4), "flat_psf": 14000, "house_psf": 17000, "yield": 0.066},
    {"name": "Bahria Town Karachi", "aliases": ["Bahria Town", "BTK", "Bahria Precinct 15"], "lat": 25.018, "lon": 67.318, "tier": "planned", "plot_120_cr": (0.8, 1.2), "flat_psf": 7000, "house_psf": 11000, "yield": 0.07},
    {"name": "Scheme 33", "aliases": ["Scheme-33", "Saadi Town"], "lat": 24.945, "lon": 67.168, "tier": "emerging", "plot_120_cr": (0.55, 0.95), "flat_psf": 11000, "house_psf": 13000, "yield": 0.075},
    {"name": "Malir", "aliases": ["Malir Halt", "malir"], "lat": 24.893, "lon": 67.195, "tier": "emerging", "plot_120_cr": (0.45, 0.85), "flat_psf": 10000, "house_psf": 12000, "yield": 0.078},
    {"name": "Shah Faisal Town", "aliases": ["Shah Faisal", "SF Town"], "lat": 24.878, "lon": 67.152, "tier": "emerging", "plot_120_cr": (0.5, 0.9), "flat_psf": 10000, "house_psf": 12500, "yield": 0.074},
    {"name": "North Karachi", "aliases": ["N. Karachi"], "lat": 24.978, "lon": 67.058, "tier": "value", "plot_120_cr": (0.4, 0.7), "flat_psf": 8000, "house_psf": 10000, "yield": 0.08},
    {"name": "Garden West", "aliases": ["Garden", "Garden East"], "lat": 24.853, "lon": 67.012, "tier": "mid", "plot_120_cr": (0.9, 1.6), "flat_psf": 15000, "house_psf": 19000, "yield": 0.063},
    {"name": "Naya Nazimabad", "aliases": ["New Nazimabad"], "lat": 24.972, "lon": 67.018, "tier": "planned", "plot_120_cr": (0.7, 1.2), "flat_psf": 15000, "house_psf": 17000, "yield": 0.06},
    {"name": "Askari 4", "aliases": ["Askari-IV", "Askari IV"], "lat": 24.898, "lon": 67.112, "tier": "mid", "plot_120_cr": (1.4, 2.2), "flat_psf": 17000, "house_psf": 21000, "yield": 0.058},
    {"name": "Korangi", "aliases": ["Korangi Creek", "korangi"], "lat": 24.838, "lon": 67.142, "tier": "value", "plot_120_cr": (0.35, 0.65), "flat_psf": 7500, "house_psf": 9500, "yield": 0.082},
    {"name": "Shahrah-e-Faisal", "aliases": ["Shahra-e-Faisal", "Main Shahrah e Faisal"], "lat": 24.873, "lon": 67.088, "tier": "commercial", "plot_120_cr": (2.0, 4.0), "flat_psf": 16000, "house_psf": 23000, "yield": 0.095},
    {"name": "Saddar", "aliases": ["Saddar Town", "saddar"], "lat": 24.861, "lon": 67.018, "tier": "commercial", "plot_120_cr": (1.5, 3.0), "flat_psf": 14000, "house_psf": 20000, "yield": 0.09},
]

AGENCIES = [
    "Zameen Associates", "Clifton Homes", "DHA Brokers", "Karachi Property Hub",
    "Bahria Consultants", "Gulshan Estate", "Skyline Realtors", "Harbour Properties",
    "Private", "N/A", "",
]
AGENTS = ["Ahmed Khan", "Sara Ali", "Imran Sheikh", "Fatima Noor", "Usman Raza", "Call Agent", None]
SOURCES = ["Zameen.com", "Graana", "OLX", "Zameen.com ", "zameen"]
FURNISHING = ["Unfurnished", "Semi-Furnished", "Furnished", "un furnished", ""]
TYPES_SALE = ["House", "Flat", "Plot", "Penthouse", "Commercial", "Upper Portion"]
TYPES_RENT = ["House", "Flat", "Upper Portion", "Lower Portion", "Penthouse", "Commercial"]


def _messy_price(pkr: float, purpose: str, rng: random.Random) -> str:
    style = rng.choice(["int", "comma", "crore", "lac", "rs", "blank", "call", "mixed"])
    if style == "blank" and rng.random() < 0.4:
        return rng.choice(["", "N/A", "NA", "-"])
    if style == "call" and rng.random() < 0.5:
        return "Call for price"
    if purpose == "For Rent":
        if style == "lac":
            return f"{pkr / 100_000:.1f} Lac"
        if style == "rs":
            return f"Rs. {int(pkr):,}"
        if style == "comma":
            return f"{int(pkr):,}"
        return str(int(pkr))
    crore = pkr / 10_000_000
    lac = pkr / 100_000
    if style == "crore":
        return f"{crore:.2f} Crore"
    if style == "lac":
        return f"{lac:.0f} Lac"
    if style == "rs":
        return f"PKR {int(pkr):,}"
    if style == "mixed":
        return f"PKR {crore:.2f} Cr"
    if style == "comma":
        return f"{int(pkr):,}"
    return str(int(pkr))


def _messy_area(sqyd: float, ptype: str, rng: random.Random) -> tuple[str, str]:
    if ptype in {"Flat", "Penthouse", "Commercial"} and rng.random() < 0.7:
        sqft = sqyd * 9
        unit = rng.choice(["Sq. Ft.", "sqft", "Sq Ft", "Square Feet"])
        return f"{int(sqft)}", unit
    unit = rng.choice(["Sq. Yd.", "Sq Yd", "sq yards", "Marla", "Gazz"])
    if unit == "Marla":
        return f"{sqyd / 30.25:.1f}", unit
    return f"{int(sqyd)}" if rng.random() < 0.7 else f"{sqyd:.1f}", unit


def _sale_price(area: dict, ptype: str, sqyd: float, beds: int, rng: random.Random) -> float:
    noise = rng.uniform(0.82, 1.22)
    if ptype == "Plot":
        lo, hi = area["plot_120_cr"]
        return ((lo + hi) / 2) * 10_000_000 * (sqyd / 120) * noise
    if ptype == "Commercial":
        return area["flat_psf"] * 1.35 * sqyd * 9 * noise
    if ptype in {"Flat", "Penthouse", "Upper Portion"}:
        psf = area["flat_psf"] * (1.15 if ptype == "Penthouse" else 1.0)
        return psf * sqyd * 9 * noise * (0.95 + 0.03 * beds)
    return area["house_psf"] * sqyd * 9 * noise


def _rent_price(sale: float, area: dict, ptype: str, rng: random.Random) -> float:
    y = area["yield"] * rng.uniform(0.85, 1.18)
    if ptype == "Commercial":
        y *= 1.45
    if ptype in {"Upper Portion", "Lower Portion"}:
        y *= 1.15
    monthly = sale * y / 12
    return max(15_000, monthly)


def generate(n_sale: int = 2200, n_rent: int = 1400, seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = random.Random(seed)
    np.random.seed(seed)
    start = datetime(2024, 6, 1)

    def row(i: int, purpose: str) -> dict:
        area = rng.choice(AREAS)
        loc = area["name"] if rng.random() > 0.18 else rng.choice(area["aliases"])
        ptype = rng.choice(TYPES_SALE if purpose == "For Sale" else TYPES_RENT)
        if ptype == "Plot":
            sqyd = rng.choice([60, 80, 120, 200, 240, 500, 1000])
            beds = bathrooms = 0
        elif ptype in {"Flat", "Penthouse"}:
            beds = rng.choice([1, 2, 2, 3, 3, 4])
            sqyd = {1: 70, 2: 120, 3: 180, 4: 240}[beds] * rng.uniform(0.85, 1.2)
            bathrooms = max(1, beds - rng.choice([0, 0, 1]))
        elif ptype == "Commercial":
            sqyd = rng.choice([50, 80, 120, 200, 300]) * rng.uniform(0.9, 1.15)
            beds = 0
            bathrooms = rng.choice([1, 2, 3])
        else:
            beds = rng.choice([2, 3, 3, 4, 5, 6])
            sqyd = rng.choice([120, 200, 240, 400, 500]) * rng.uniform(0.9, 1.1)
            bathrooms = beds - rng.choice([0, 1])

        sale = _sale_price(area, ptype, sqyd, beds, rng)
        price = sale if purpose == "For Sale" else _rent_price(sale, area, ptype, rng)
        area_val, area_unit = _messy_area(sqyd, ptype, rng)
        listed = start + timedelta(days=rng.randint(0, 500))
        date_fmt = rng.choice(["iso", "dmy", "us", "text"])
        if date_fmt == "iso":
            date_s = listed.strftime("%Y-%m-%d")
        elif date_fmt == "dmy":
            date_s = listed.strftime("%d/%m/%Y")
        elif date_fmt == "us":
            date_s = listed.strftime("%m-%d-%Y")
        else:
            date_s = listed.strftime("%d %b %Y")

        pid = f"KHI-{100000 + i}"
        if rng.random() < 0.02:
            pid = f"KHI-{100000 + rng.randint(0, max(1, i - 1))}"

        return {
            "property_id": pid,
            "title": f"{ptype} in {area['name']}" if rng.random() > 0.1 else f"{beds} Bed {ptype} {loc}",
            "purpose": purpose if rng.random() > 0.04 else purpose.upper(),
            "property_type": ptype if rng.random() > 0.08 else ptype.lower(),
            "city": rng.choice(["Karachi", "karachi", "Karachi ", "KHI"]),
            "location": loc,
            "area": area_val,
            "area_unit": area_unit,
            "bedrooms": "" if (ptype == "Plot" or rng.random() < 0.05) else beds,
            "bathrooms": "" if rng.random() < 0.07 else bathrooms,
            "price": _messy_price(price, purpose, rng),
            "latitude": round(area["lat"] + rng.uniform(-0.012, 0.012), 6) if rng.random() > 0.06 else "",
            "longitude": round(area["lon"] + rng.uniform(-0.012, 0.012), 6) if rng.random() > 0.06 else "",
            "agency": rng.choice(AGENCIES),
            "agent": rng.choice(AGENTS),
            "listing_date": date_s,
            "year_built": rng.choice(["", "2010", "2015", "2018", "2020", "2022", "2024", "N/A"]),
            "parking": rng.choice(["Yes", "No", "1", "2", "Covered", ""]),
            "furnishing": rng.choice(FURNISHING),
            "source": rng.choice(SOURCES),
            "description": rng.choice([
                "Corner plot, west open.",
                "Near park and mosque.",
                "Investor deal, documents clear.",
                "Luxury finishing, sea view.",
                "",
                "Urgent sale. Possession.",
            ]),
        }

    sale_rows = [row(i, "For Sale") for i in range(n_sale)]
    rent_rows = [row(n_sale + i, "For Rent") for i in range(n_rent)]
    return pd.DataFrame(sale_rows), pd.DataFrame(rent_rows)


def write_raw(n_sale: int = 2200, n_rent: int = 1400) -> tuple[Path, Path]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sale, rent = generate(n_sale, n_rent)
    sale.to_csv(RAW_SALE_CSV, index=False)
    rent.to_csv(RAW_RENT_CSV, index=False)
    return RAW_SALE_CSV, RAW_RENT_CSV


if __name__ == "__main__":
    s, r = write_raw()
    print(f"Wrote {s}")
    print(f"Wrote {r}")
