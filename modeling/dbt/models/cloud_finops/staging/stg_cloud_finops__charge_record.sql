-- Staging: light typing on cloud_finops.charge_record (FOCUS-shaped).
{{ config(materialized='view') }}

select
    cast(charge_record_id            as varchar)   as charge_record_id,
    cast(billing_account_id          as varchar)   as billing_account_id,
    cast(provider                    as varchar)   as provider,
    cast(service_name                as varchar)   as service_name,
    cast(service_category            as varchar)   as service_category,
    cast(service_subcategory         as varchar)   as service_subcategory,
    cast(region_id                   as varchar)   as region_id,
    cast(resource_id                 as varchar)   as resource_id,
    cast(resource_type               as varchar)   as resource_type,
    cast(charge_period_start         as timestamp) as charge_period_start,
    cast(charge_period_end           as timestamp) as charge_period_end,
    cast(charge_category             as varchar)   as charge_category,
    cast(charge_class                as varchar)   as charge_class,
    cast(pricing_unit                as varchar)   as pricing_unit,
    cast(pricing_quantity            as double)    as pricing_quantity,
    cast(list_unit_price             as double)    as list_unit_price,
    cast(list_cost                   as double)    as list_cost,
    cast(billed_cost                 as double)    as billed_cost,
    cast(effective_cost              as double)    as effective_cost,
    upper(billing_currency)                        as billing_currency,
    cast(commitment_discount_id      as varchar)   as commitment_discount_id,
    cast(commitment_discount_category as varchar)  as commitment_discount_category,
    cast(tag_environment             as varchar)   as tag_environment,
    cast(tag_team                    as varchar)   as tag_team,
    cast({{ format_date('charge_period_start', '%Y%m%d') }} as integer) as charge_date_key
from {{ source('cloud_finops', 'charge_record') }}
