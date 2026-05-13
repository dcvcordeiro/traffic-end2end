-- TODO (Block 3): implement silver_traffic_monthly.
--
-- See docs/capstone/day-1/block-3-modeling.md → "Suggested Silver model".
-- Replace the body below with your model. Read from
-- {{ ref('stg_toll_traffic') }}, apply the cleanups (date parse,
-- direction harmonisation, negative-volume decision), and aggregate to
-- the chosen grain so the uniqueness test in `_silver.yml` holds.
--
-- Expected output columns:
--   plaza_name, concessionaria, direction, vehicle_type,
--   month_start, volume_total

select
    null::text    as plaza_name,
    null::text    as concessionaria,
    null::text    as direction,
    null::text    as vehicle_type,
    null::date    as month_start,
    null::integer as volume_total
where false
