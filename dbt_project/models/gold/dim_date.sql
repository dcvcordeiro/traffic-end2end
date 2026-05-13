-- Date dimension at month grain. Spans the months observed in Silver.

with bounds as (

    select
        date_trunc('month', min(month_start))::date as min_month,
        date_trunc('month', max(month_start))::date as max_month
    from {{ ref('silver_traffic_monthly') }}

),

months as (

    {{ dbt_utils.date_spine(
        datepart="month",
        start_date="cast('2010-01-01' as date)",
        end_date="cast('2020-01-01' as date)"
    ) }}

),

filtered as (

    select date_month::date as month_start
    from months
    cross join bounds
    where date_month::date between bounds.min_month and bounds.max_month

)

select
    {{ dbt_utils.generate_surrogate_key(['month_start']) }} as date_key,
    month_start,
    extract(year    from month_start)::int as year,
    extract(quarter from month_start)::int as quarter,
    extract(month   from month_start)::int as month,
    to_char(month_start, 'YYYY-MM')        as year_month
from filtered
