-- Plaza dimension. One row per plaza_name. Each plaza has exactly one
-- concessionaire across the dataset (verified in Block 1).

with distinct_plazas as (

    select distinct
        plaza_name,
        concessionaria
    from {{ ref('silver_traffic_monthly') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['plaza_name']) }} as plaza_key,
    plaza_name,
    concessionaria
from distinct_plazas
