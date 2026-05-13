-- Silver: clean rows ready for star-schema joins.
--
-- Decisions captured here:
--   1. mes_ano (Mon-YY) parses to a real DATE (first day of month). The
--      two-digit year window is corrected so 'Jan-10' resolves to 2010,
--      not 1910.
--   2. Negative volume_total rows (3 in source) are dropped; this is
--      flagged in the Gold contract as a known caveat.
--   3. Categoria is dropped: tipo_de_veiculo carries the same signal
--      with three clean values instead of forty-six messy ones.
--   4. Sentido is left as-is; harmonizing across concessionaires would
--      need a manual lookup the dataset does not carry.
--   5. The model aggregates to the chosen grain so the uniqueness test
--      below holds and Gold can pass volume through without re-summing.

with cleaned as (

    select
        btrim(praca)               as plaza_name,
        btrim(concessionaria)      as concessionaria,
        btrim(sentido)             as direction,
        btrim(tipo_de_veiculo)     as vehicle_type,
        to_date(mes_ano, 'Mon-YY') as raw_month,
        volume_total
    from {{ ref('stg_toll_traffic') }}
    where volume_total >= 0

),

dated as (

    -- Postgres' Mon-YY parser puts 'Jan-10' into 1910. Anything before
    -- 1950 is a two-digit-year rollover artifact — push forward 100y.
    select
        plaza_name,
        concessionaria,
        direction,
        vehicle_type,
        case
            when extract(year from raw_month) < 1950
                then raw_month + interval '100 years'
            else raw_month
        end::date as month_start,
        volume_total
    from cleaned

),

aggregated as (

    select
        plaza_name,
        concessionaria,
        direction,
        vehicle_type,
        month_start,
        sum(volume_total)::integer as volume_total
    from dated
    group by 1, 2, 3, 4, 5

)

select * from aggregated
