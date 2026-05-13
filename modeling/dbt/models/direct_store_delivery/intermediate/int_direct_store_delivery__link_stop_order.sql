{{ config(materialized='ephemeral') }}

with orders as (select * from {{ ref('stg_direct_store_delivery__dsd_order') }})

select
    md5(coalesce(order_id,'') || '|' || coalesce(stop_id,'')) as h_link_hk,
    md5(stop_id)                                              as h_stop_hk,
    md5(order_id)                                             as h_order_hk,
    current_date                                              as load_date,
    'direct_store_delivery.dsd_order'                         as record_source
from orders
where order_id is not null and stop_id is not null
