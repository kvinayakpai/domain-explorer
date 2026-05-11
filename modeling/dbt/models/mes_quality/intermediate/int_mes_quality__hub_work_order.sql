-- Vault hub for Work Order.
{{ config(materialized='ephemeral') }}

with src as (
    select work_order_id, started_at from {{ ref('stg_mes_quality__work_orders') }}
    where work_order_id is not null
)

select
    md5(work_order_id)               as h_work_order_hk,
    work_order_id                    as work_order_bk,
    min(started_at)                  as load_ts,
    'mes_quality.work_orders'        as record_source
from src
group by work_order_id
