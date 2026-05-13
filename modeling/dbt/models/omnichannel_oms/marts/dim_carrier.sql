{{ config(materialized='table') }}

with c as (
    select distinct carrier from {{ ref('stg_omnichannel_oms__shipments') }}
)
select
    row_number() over (order by carrier) as carrier_sk,
    carrier,
    case carrier
        when 'fedex'         then 'ground'
        when 'ups'           then 'ground'
        when 'usps'          then 'priority'
        when 'dhl'           then 'express'
        when 'store_courier' then 'same_day'
        when 'ontrac'        then 'ground'
        when 'lasership'     then 'ground'
        when 'same_day'      then 'same_day'
        else 'ground'
    end as service_default
from c
