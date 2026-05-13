-- Supplier dimension. D&B DUNS + LEI carried as natural attributes;
-- supplier_sk is the surrogate for facts.
{{ config(materialized='table') }}

select
    row_number() over (order by supplier_id) as supplier_sk,
    supplier_id,
    duns_number,
    lei,
    legal_name,
    parent_duns,
    country_iso2,
    region,
    industry_naics,
    diversity_flags,
    ecovadis_score,
    ecovadis_medal,
    cdp_climate_score,
    sbti_committed,
    paydex_score,
    failure_score,
    cyber_score,
    critical_flag,
    sanctions_flag,
    status,
    cast(onboarded_at as timestamp)         as valid_from,
    cast(null as timestamp)                 as valid_to,
    true                                    as is_current
from {{ ref('stg_procurement_spend_analytics__supplier') }}
