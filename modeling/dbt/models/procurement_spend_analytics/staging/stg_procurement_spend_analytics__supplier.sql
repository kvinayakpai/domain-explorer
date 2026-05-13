{{ config(materialized='view') }}

select
    cast(supplier_id          as varchar)    as supplier_id,
    cast(duns_number          as varchar)    as duns_number,
    cast(lei                  as varchar)    as lei,
    cast(legal_name           as varchar)    as legal_name,
    cast(parent_duns          as varchar)    as parent_duns,
    cast(tax_id               as varchar)    as tax_id,
    cast(country_iso2         as varchar)    as country_iso2,
    cast(region               as varchar)    as region,
    cast(industry_naics       as varchar)    as industry_naics,
    cast(industry_sic         as varchar)    as industry_sic,
    cast(diversity_flags      as varchar)    as diversity_flags,
    cast(ecovadis_score       as smallint)   as ecovadis_score,
    cast(ecovadis_medal       as varchar)    as ecovadis_medal,
    cast(cdp_climate_score    as varchar)    as cdp_climate_score,
    cast(sbti_committed       as boolean)    as sbti_committed,
    cast(paydex_score         as smallint)   as paydex_score,
    cast(failure_score        as smallint)   as failure_score,
    cast(cyber_score          as smallint)   as cyber_score,
    cast(critical_flag        as boolean)    as critical_flag,
    cast(sanctions_flag       as boolean)    as sanctions_flag,
    cast(status               as varchar)    as status,
    cast(onboarded_at         as timestamp)  as onboarded_at,
    cast(last_assessment_at   as timestamp)  as last_assessment_at,
    case
        when ecovadis_medal in ('silver', 'gold', 'platinum') then true
        else false
    end as is_sustainable_silver_plus,
    case
        when ecovadis_medal in ('gold', 'platinum') then true
        else false
    end as is_sustainable_gold_plus
from {{ source('procurement_spend_analytics', 'supplier') }}
