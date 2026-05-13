-- Vault satellite — descriptive attributes for customer_master.
{{ config(materialized='ephemeral') }}

select
    md5(customer_id)                              as h_customer_hk,
    updated_at                                    as load_dts,
    email_sha256,
    phone_sha256,
    country_iso2,
    postal_code,
    lifecycle_stage,
    golden_record_source,
    confidence_score,
    resolution_method,
    status,
    'customer_loyalty_cdp.customer_master'        as record_source
from {{ ref('stg_customer_loyalty_cdp__customer_master') }}
