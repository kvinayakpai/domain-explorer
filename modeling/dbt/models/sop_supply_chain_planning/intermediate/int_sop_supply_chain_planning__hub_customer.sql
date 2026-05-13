-- Vault hub for the Customer business key.
{{ config(materialized='ephemeral') }}

with src as (
    select distinct customer_id
    from {{ ref('stg_sop_supply_chain_planning__customers') }}
    where customer_id is not null
)

select
    md5(customer_id)                          as h_customer_hk,
    customer_id                                as customer_bk,
    current_date                               as load_date,
    'sop_supply_chain_planning.customer'       as record_source
from src
