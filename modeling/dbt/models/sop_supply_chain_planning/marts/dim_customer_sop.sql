-- Customer / channel dimension. Suffix `_sop` avoids collision.
{{ config(materialized='table') }}

select
    row_number() over (order by customer_id) as customer_sk,
    customer_id,
    customer_name,
    channel,
    segment,
    country_iso2,
    region,
    priority,
    status
from {{ ref('stg_sop_supply_chain_planning__customers') }}
