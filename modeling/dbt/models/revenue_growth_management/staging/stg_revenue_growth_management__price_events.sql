{{ config(materialized='view') }}

select
    cast(price_event_id           as varchar)   as price_event_id,
    cast(account_id               as varchar)   as account_id,
    cast(pack_id                  as varchar)   as pack_id,
    cast(event_type               as varchar)   as event_type,
    cast(prior_list_price_cents   as bigint)    as prior_list_price_cents,
    cast(new_list_price_cents     as bigint)    as new_list_price_cents,
    cast(prior_srp_cents          as bigint)    as prior_srp_cents,
    cast(new_srp_cents            as bigint)    as new_srp_cents,
    upper(currency)                              as currency,
    cast(announced_at             as timestamp) as announced_at,
    cast(effective_from           as date)      as effective_from,
    cast(source_system            as varchar)   as source_system,
    cast(approver_role            as varchar)   as approver_role,
    cast(new_list_price_cents - prior_list_price_cents as bigint) as price_delta_cents,
    case
        when prior_list_price_cents > 0
            then (cast(new_list_price_cents - prior_list_price_cents as double) / prior_list_price_cents)
    end as price_delta_pct
from {{ source('revenue_growth_management', 'price_event') }}
