{{ config(materialized='view') }}

select
    cast(order_id                as varchar)  as order_id,
    cast(stop_id                 as varchar)  as stop_id,
    cast(outlet_id               as varchar)  as outlet_id,
    cast(order_type              as varchar)  as order_type,
    cast(order_date              as date)     as order_date,
    cast(requested_delivery_date as date)     as requested_delivery_date,
    cast(account_id              as varchar)  as account_id,
    cast(salesman_id             as varchar)  as salesman_id,
    cast(total_cases             as integer)  as total_cases,
    cast(total_units             as integer)  as total_units,
    cast(gross_amount_cents      as bigint)   as gross_amount_cents,
    cast(discount_amount_cents   as bigint)   as discount_amount_cents,
    cast(net_amount_cents        as bigint)   as net_amount_cents,
    cast(tax_amount_cents        as bigint)   as tax_amount_cents,
    cast(payment_terms           as varchar)  as payment_terms,
    cast(status                  as varchar)  as status,
    cast(created_at              as timestamp) as created_at,
    case when order_type = 'presell' then true else false end as is_presell,
    case when order_type = 'swap'    then true else false end as is_swap
from {{ source('direct_store_delivery', 'dsd_order') }}
