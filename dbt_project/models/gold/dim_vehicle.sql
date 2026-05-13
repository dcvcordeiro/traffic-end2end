-- TODO (Block 3): implement dim_vehicle.
--
-- See docs/capstone/day-1/block-3-modeling.md → "dim_vehicle".
-- One row per `vehicle_type`. With the recommended grain you get three
-- rows: Comercial, Moto, Passeio. Use `dbt_utils.generate_surrogate_key`
-- for `vehicle_key`.
--
-- Expected columns:
--   vehicle_key, vehicle_type

select
    null::text as vehicle_key,
    null::text as vehicle_type
where false
