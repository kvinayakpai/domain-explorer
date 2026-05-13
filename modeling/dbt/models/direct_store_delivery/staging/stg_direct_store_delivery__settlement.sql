{{ config(materialized='view') }}

select
    cast(settlement_id              as varchar)  as settlement_id,
    cast(route_id                   as varchar)  as route_id,
    cast(driver_id                  as varchar)  as driver_id,
    cast(vehicle_id                 as varchar)  as vehicle_id,
    cast(settlement_date            as date)     as settlement_date,
    cast(total_invoiced_cents       as bigint)   as total_invoiced_cents,
    cast(total_collected_cash_cents as bigint)   as total_collected_cash_cents,
    cast(total_collected_check_cents as bigint)  as total_collected_check_cents,
    cast(total_collected_eft_cents  as bigint)   as total_collected_eft_cents,
    cast(total_charge_account_cents as bigint)   as total_charge_account_cents,
    cast(returns_credit_cents       as bigint)   as returns_credit_cents,
    cast(spoilage_credit_cents      as bigint)   as spoilage_credit_cents,
    cast(variance_cents             as bigint)   as variance_cents,
    cast(variance_reason            as varchar)  as variance_reason,
    cast(status                     as varchar)  as status,
    cast(closed_at                  as timestamp) as closed_at,
    cast(approved_by                as varchar)  as approved_by,
    abs(variance_cents)                          as abs_variance_cents,
    case when abs(variance_cents) <= 2500 then true else false end as is_balanced
from {{ source('direct_store_delivery', 'settlement') }}
