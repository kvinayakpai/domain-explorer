-- Vault-style satellite carrying descriptive Charge Record attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_cloud_finops__charge_record') }}
)

select
    md5(charge_record_id)                                   as h_charge_hk,
    charge_period_start                                     as load_ts,
    md5(coalesce(provider,'') || '|' || coalesce(service_name,'') || '|'
        || coalesce(charge_category,'') || '|' || cast(billed_cost as varchar))
                                                            as hashdiff,
    provider,
    service_name,
    service_category,
    service_subcategory,
    region_id,
    resource_id,
    resource_type,
    charge_period_start,
    charge_period_end,
    charge_category,
    charge_class,
    pricing_unit,
    pricing_quantity,
    list_unit_price,
    list_cost,
    billed_cost,
    effective_cost,
    billing_currency,
    commitment_discount_id,
    commitment_discount_category,
    tag_environment,
    tag_team,
    'cloud_finops.charge_record'                            as record_source
from src
