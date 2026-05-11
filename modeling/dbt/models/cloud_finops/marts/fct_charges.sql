-- Grain: one row per FOCUS ChargeRecord.
-- FKs: billing_account_key, service_key, region_key, charge_date_key.
{{ config(materialized='table') }}

with sat as (select * from {{ ref('int_cloud_finops__sat_charge') }}),
     hub as (select * from {{ ref('int_cloud_finops__hub_charge') }}),
     l_ca as (select * from {{ ref('int_cloud_finops__link_charge_billing_account') }})

select
    h.h_charge_hk                                       as charge_key,
    h.charge_bk                                         as charge_record_id,
    l_ca.h_billing_account_hk                           as billing_account_key,
    md5(s.provider || '|' || s.service_name)            as service_key,
    md5(s.provider || '|' || s.region_id)               as region_key,
    cast({{ format_date('s.charge_period_start', '%Y%m%d') }} as integer) as charge_date_key,
    s.provider,
    s.service_name,
    s.service_category,
    s.service_subcategory,
    s.region_id,
    s.resource_id,
    s.resource_type,
    s.charge_period_start,
    s.charge_period_end,
    s.charge_category,
    s.charge_class,
    s.pricing_unit,
    s.pricing_quantity,
    s.list_unit_price,
    s.list_cost,
    s.billed_cost,
    s.effective_cost,
    s.list_cost - s.effective_cost                       as discount_amount,
    case when s.list_cost > 0
         then round((s.list_cost - s.effective_cost) / s.list_cost, 4)
         else null end                                   as discount_pct,
    s.billing_currency,
    s.commitment_discount_id,
    s.commitment_discount_category,
    s.tag_environment,
    s.tag_team,
    case when s.tag_environment = 'untagged' then true else false end as is_untagged
from hub h
join sat   s    on s.h_charge_hk    = h.h_charge_hk
left join l_ca  on l_ca.h_charge_hk = h.h_charge_hk
