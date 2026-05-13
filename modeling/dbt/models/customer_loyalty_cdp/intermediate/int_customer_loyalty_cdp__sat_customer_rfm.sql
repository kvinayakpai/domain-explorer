-- Vault satellite — RFM + predictive scores for customer_master.
{{ config(materialized='ephemeral') }}

select
    md5(customer_id)                              as h_customer_hk,
    updated_at                                    as load_dts,
    rfm_recency,
    rfm_frequency,
    rfm_monetary,
    predicted_clv,
    predicted_churn_prob,
    'customer_loyalty_cdp.customer_master'        as record_source
from {{ ref('stg_customer_loyalty_cdp__customer_master') }}
