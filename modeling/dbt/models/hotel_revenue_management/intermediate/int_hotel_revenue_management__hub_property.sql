-- Vault-style hub for Property.
{{ config(materialized='ephemeral') }}

with src as (
    select property_id from {{ ref('stg_hotel_revenue_management__properties') }}
    where property_id is not null
    union
    select distinct property_id from {{ ref('stg_hotel_revenue_management__reservations') }}
    where property_id is not null
)

select
    md5(property_id)                          as h_property_hk,
    property_id                               as property_bk,
    current_date                              as load_date,
    'hotel_revenue_management.properties'     as record_source
from src
group by property_id
