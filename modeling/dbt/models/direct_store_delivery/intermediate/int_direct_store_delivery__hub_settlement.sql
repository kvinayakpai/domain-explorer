{{ config(materialized='ephemeral') }}

with src as (
    select settlement_id from {{ ref('stg_direct_store_delivery__settlement') }}
    where settlement_id is not null
)

select
    md5(settlement_id)                  as h_settlement_hk,
    settlement_id                       as settlement_bk,
    current_date                        as load_date,
    'direct_store_delivery.settlement'  as record_source
from src
group by settlement_id
