{{ config(materialized='ephemeral') }}

with src as (
    select stop_id from {{ ref('stg_direct_store_delivery__stop') }}
    where stop_id is not null
)

select
    md5(stop_id)                        as h_stop_hk,
    stop_id                             as stop_bk,
    current_date                        as load_date,
    'direct_store_delivery.stop'        as record_source
from src
group by stop_id
