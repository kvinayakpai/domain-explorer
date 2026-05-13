-- Vault hub for the Customer business key.
{{ config(materialized='ephemeral') }}

with src as (
    select customer_id
    from {{ ref('stg_returns_reverse_logistics__customers') }}
    where customer_id is not null
)

select
    md5(customer_id)                                as hk_customer,
    customer_id                                     as customer_bk,
    current_date                                    as load_dts,
    'returns_reverse_logistics.customer'            as record_source
from src
group by customer_id
