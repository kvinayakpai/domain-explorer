-- Vault satellite: Work Order mutable state.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_mes_quality__work_orders') }})

select
    md5(work_order_id)                                                       as h_work_order_hk,
    started_at                                                               as load_ts,
    md5(coalesce(status,'') || '|' || cast(coalesce(qty_planned, 0) as varchar)
        || '|' || cast(coalesce(qty_produced, 0) as varchar))                 as hashdiff,
    product_code,
    qty_planned,
    qty_produced,
    started_at,
    ended_at,
    status,
    'mes_quality.work_orders'                                                 as record_source
from src
