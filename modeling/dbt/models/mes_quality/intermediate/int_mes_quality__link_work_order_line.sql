-- Vault link: Work Order → Line.
{{ config(materialized='ephemeral') }}

with src as (
    select work_order_id, line_id from {{ ref('stg_mes_quality__work_orders') }}
    where work_order_id is not null and line_id is not null
)

select
    md5(work_order_id || '|' || line_id) as l_work_order_line_hk,
    md5(work_order_id)                   as h_work_order_hk,
    md5(line_id)                         as h_line_hk,
    current_date                         as load_date,
    'mes_quality.work_orders'            as record_source
from src
group by work_order_id, line_id
