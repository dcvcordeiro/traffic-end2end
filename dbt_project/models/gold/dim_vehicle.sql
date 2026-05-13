-- Vehicle dimension. Three rows: Comercial, Moto, Passeio.

with distinct_vehicles as (

    select distinct vehicle_type
    from {{ ref('silver_traffic_monthly') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['vehicle_type']) }} as vehicle_key,
    vehicle_type
from distinct_vehicles
