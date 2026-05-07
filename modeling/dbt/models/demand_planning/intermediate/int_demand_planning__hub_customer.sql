-- Vault-style hub for B2B Customer.
{{ config(materialized='ephemeral') }}

with src as (
    select customer_id from {{ ref('stg_demand_planning__customers_b2b') }}
    where customer_id is not null
    union
    select distinct customer_id from {{ ref('stg_demand_planning__shipments') }}
    where customer_id is not null
)

select
    md5(customer_id)                 as h_customer_hk,
    customer_id                      as customer_bk,
    current_date                     as load_date,
    'demand_planning.customers_b2b'  as record_source
from src
group by customer_id
