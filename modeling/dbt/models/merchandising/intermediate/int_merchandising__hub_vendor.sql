-- Vault-style hub for Vendor.
{{ config(materialized='ephemeral') }}

with src as (
    select vendor_id from {{ ref('stg_merchandising__vendors') }}
    where vendor_id is not null
    union
    select distinct vendor_id from {{ ref('stg_merchandising__products') }}
    where vendor_id is not null
)

select
    md5(vendor_id)            as h_vendor_hk,
    vendor_id                 as vendor_bk,
    current_date              as load_date,
    'merchandising.vendors'   as record_source
from src
group by vendor_id
