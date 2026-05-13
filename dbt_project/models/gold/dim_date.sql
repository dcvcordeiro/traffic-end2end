-- TODO (Block 3): implement dim_date.
--
-- See docs/capstone/day-1/block-3-modeling.md → "dim_date".
-- Generate one row per month between the earliest and latest
-- `month_start` in `silver_traffic_monthly`. Use `dbt_utils.date_spine`.
--
-- Expected columns:
--   date_key (surrogate via dbt_utils.generate_surrogate_key),
--   month_start, year, quarter, month, year_month

select
    null::text    as date_key,
    null::date    as month_start,
    null::integer as year,
    null::integer as quarter,
    null::integer as month,
    null::text    as year_month
where false
