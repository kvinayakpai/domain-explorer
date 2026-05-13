-- Vault hub for the Customer business key.
{{ config(materialized='ephemeral') }}

with src as (
    select customer_id
    from {{ ref('stg_customer_loyalty_cdp__customer_master') }}
    where customer_id is not null
)

select
    md5(customer_id)                                  as h_customer_hk,
    customer_id                                       as customer_bk,
    current_date                                      as load_date,
    'customer_loyalty_cdp.customer_master'            as record_source
from src
group by customer_id
