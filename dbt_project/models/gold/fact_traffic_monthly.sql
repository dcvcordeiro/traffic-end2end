-- Fact: monthly traffic volume.
-- Grain: one row per (plaza, direction, vehicle_type, month_start).
-- Volume passes through unchanged from Silver — Silver did the rollup.

with silver as (

    select * from {{ ref('silver_traffic_monthly') }}

),

joined as (

    select
        d.date_key,
        p.plaza_key,
        v.vehicle_key,
        s.direction,
        s.volume_total
    from silver as s
    join {{ ref('dim_date')    }} as d on d.month_start  = s.month_start
    join {{ ref('dim_plaza')   }} as p on p.plaza_name   = s.plaza_name
    join {{ ref('dim_vehicle') }} as v on v.vehicle_type = s.vehicle_type

)

select * from joined
