-- Vault satellite carrying descriptive Supplier attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_procurement_spend_analytics__supplier') }})

select
    md5(supplier_id)                                                            as h_supplier_hk,
    cast(onboarded_at as timestamp)                                             as load_ts,
    md5(coalesce(legal_name,'') || '|' || coalesce(country_iso2,'') || '|'
        || coalesce(ecovadis_medal,'') || '|' || cast(coalesce(ecovadis_score, 0) as varchar)
        || '|' || cast(coalesce(paydex_score, 0) as varchar)
        || '|' || coalesce(status,''))                                          as hashdiff,
    legal_name,
    parent_duns,
    tax_id,
    country_iso2,
    region,
    industry_naics,
    industry_sic,
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
    'procurement_spend_analytics.supplier'                                       as record_source
from src
