# Power BI model

## Files to import

From `powerbi/exports/` after `python -m src.pipeline`:

- `fact_sale.csv`
- `fact_rent.csv`
- `fact_yield.csv`

Or connect to `data/sql/karachi_real_estate.db` (SQLite).

## Relationships

- `fact_yield.location_std` → distinct locations from `fact_sale`
- `fact_yield.property_type` → property type dimension
- Optional date table on `listing_dt`

## Suggested pages

1. Market map and KPI strip (median crore, PSF, listing count)
2. Yield heatmap: location × property type
3. Sale vs rent scatter with size buckets
4. SQL-backed table of top investment scores

Copy measures from `dax_measures.dax`.
