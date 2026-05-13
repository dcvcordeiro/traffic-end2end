-- TODO (Block 3): implement dim_plaza.
--
-- See docs/capstone/day-1/block-3-modeling.md → "dim_plaza".
-- One row per unique plaza, sourced from `silver_traffic_monthly`.
-- Use `dbt_utils.generate_surrogate_key` for `plaza_key`. Hash on the
-- combination of (concessionaria, plaza_name) — different concessionaires
-- can publish the same plaza number, so plaza_name alone is not unique.
--
-- Expected columns:
--   plaza_key, plaza_name, concessionaria
-- Optional nice-to-haves: parsed `highway` and `state` from plaza_name.

select
    null::text as plaza_key,
    null::text as plaza_name,
    null::text as concessionaria
where false
