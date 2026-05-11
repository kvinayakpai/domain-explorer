-- Vault link: Order ↔ Execution (a fill).
{{ config(materialized='ephemeral') }}

with e as (
    select execution_id, order_id from {{ ref('stg_capital_markets__execution') }}
)

select
    md5(coalesce(order_id,'') || '|' || execution_id) as l_order_execution_hk,
    case when order_id is null then null else md5(order_id) end as h_order_hk,
    execution_id                                       as exec_bk,
    current_date                                       as load_date,
    'capital_markets.execution'                        as record_source
from e
