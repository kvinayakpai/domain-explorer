{{ config(materialized='ephemeral') }}

with src as (
    select order_id from {{ ref('stg_direct_store_delivery__dsd_order') }}
    where order_id is not null
)

select
    md5(order_id)                       as h_order_hk,
    order_id                            as order_bk,
    current_date                        as load_date,
    'direct_store_delivery.dsd_order'   as record_source
from src
group by order_id
