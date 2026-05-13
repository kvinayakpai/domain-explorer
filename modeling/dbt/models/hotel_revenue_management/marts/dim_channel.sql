-- Channel dimension.
{{ config(materialized='table') }}

with stg as (select * from {{ ref('stg_hotel_revenue_management__channels') }})

select
    md5(channel_id)        as channel_key,
    channel_id,
    channel_name,
    channel_category,
    commission_pct,
    case
        when commission_pct is null      then 'unknown'
        when commission_pct < 0.05       then 'low'
        when commission_pct < 0.15       then 'mid'
        else 'high'
    end                     as commission_band,
    is_active,
    current_date            as dim_loaded_at
from stg
