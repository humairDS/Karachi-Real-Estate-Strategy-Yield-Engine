-- Ready-to-run SQL for Streamlit explorer and Power BI DirectQuery practice

-- 1. Highest gross yields
SELECT l.location_name, t.property_type, y.size_bucket,
       ROUND(y.gross_yield_pct, 2) AS gross_yield,
       ROUND(y.net_yield_pct, 2) AS net_yield,
       y.sale_listings, y.rent_listings
FROM fact_yield y
JOIN dim_location l ON l.location_id = y.location_id
JOIN dim_property_type t ON t.type_id = y.type_id
ORDER BY y.gross_yield_pct DESC
LIMIT 20;

-- 2. Median sale asking price by neighbourhood
SELECT l.location_name,
       COUNT(*) AS n,
       ROUND(AVG(f.price_pkr) / 10000000.0, 2) AS avg_crore,
       ROUND(AVG(f.price_per_sqft), 0) AS avg_psf
FROM fact_listings f
JOIN dim_location l ON l.location_id = f.location_id
WHERE f.purpose = 'For Sale'
GROUP BY l.location_name
ORDER BY avg_crore DESC;

-- 3. Rent vs sale inventory
SELECT t.property_type, f.purpose, COUNT(*) AS listings
FROM fact_listings f
JOIN dim_property_type t ON t.type_id = f.type_id
GROUP BY t.property_type, f.purpose
ORDER BY listings DESC;

-- 4. Commercial vs residential yield
SELECT t.property_type,
       ROUND(AVG(y.gross_yield_pct), 2) AS avg_gross,
       ROUND(AVG(y.net_yield_pct), 2) AS avg_net
FROM fact_yield y
JOIN dim_property_type t ON t.type_id = y.type_id
GROUP BY t.property_type
ORDER BY avg_gross DESC;
