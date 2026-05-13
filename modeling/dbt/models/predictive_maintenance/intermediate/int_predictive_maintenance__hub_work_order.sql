-- Vault hub for the Work Order business key.
{{ config(materialized='ephemeral') }}

with src as (
    select work_order_id
    from {{ ref('stg_predictive_maintenance__work_order') }}
    where work_order_id is not null
)

select
    md5(work_order_id)                          as h_work_order_hk,
    work_order_id                               as work_order_bk,
    current_date                                as load_date,
    'predictive_maintenance.work_order'         as record_source
from src
group by work_order_id
