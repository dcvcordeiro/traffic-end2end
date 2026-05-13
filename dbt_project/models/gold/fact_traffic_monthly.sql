-- TODO (Block 3): implement fact_traffic_monthly.
--
-- See docs/capstone/day-1/block-3-modeling.md → "fact_traffic_monthly".
-- Build by joining `silver_traffic_monthly` to the three dimensions on
-- their natural keys and replacing them with the surrogate keys.
-- One row per (plaza, direction, vehicle, month).
--
-- Expected columns:
--   date_key, plaza_key, vehicle_key, direction, volume_total
-- (`direction` stays on the fact as a degenerate dimension.)

select
    null::text    as date_key,
    null::text    as plaza_key,
    null::text    as vehicle_key,
    null::text    as direction,
    null::integer as volume_total
where false
