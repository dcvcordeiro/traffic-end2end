-- Staging model for the raw toll-traffic table.
--
-- Goals demonstrated here (copy this pattern when you build Silver/Gold):
--   1. Reference Bronze through the source() macro, never a hard-coded name.
--   2. Trim free-text fields so joins/filters behave predictably.
--   3. Make data types explicit; do not rely on the loader's inferred types.
--   4. Rename only when it adds clarity — keep column names predictable.
--
-- Real-world quirk: a handful of `volume_total` rows arrive as floats with
-- Portuguese decimal commas (e.g. `639204,0000000001`). We replace the
-- comma with a dot, cast to numeric, and round to integer so the column
-- type is uniform downstream.

with source as (

    select * from {{ source('bronze', 'toll_traffic_raw') }}

),

renamed as (

    select
        btrim(concessionaria)                                          as concessionaria,
        btrim(mes_ano)                                                 as mes_ano,
        btrim(sentido)                                                 as sentido,
        btrim(praca)                                                   as praca,
        btrim(categoria)                                               as categoria,
        btrim(tipo_de_veiculo)                                         as tipo_de_veiculo,
        round(replace(volume_total::text, ',', '.')::numeric)::integer as volume_total,
        _loaded_at
    from source

)

select * from renamed
