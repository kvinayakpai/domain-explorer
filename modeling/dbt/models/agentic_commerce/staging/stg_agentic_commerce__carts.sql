{{ config(materialized='view') }}

select
    cast(cart_id                  as varchar)    as cart_id,
    cast(intent_id                as varchar)    as intent_id,
    cast(merchant_id              as varchar)    as merchant_id,
    cast(subtotal_minor           as bigint)     as subtotal_minor,
    cast(tax_minor                as bigint)     as tax_minor,
    cast(shipping_minor           as bigint)     as shipping_minor,
    cast(total_minor              as bigint)     as total_minor,
    upper(currency)                                as currency,
    cast(line_count               as smallint)   as line_count,
    cast(signed_payload_hash      as varchar)    as signed_payload_hash,
    cast(signature_alg            as varchar)    as signature_alg,
    cast(built_at                 as timestamp)  as built_at,
    cast(confirmed_by_principal   as boolean)    as confirmed_by_principal,
    cast(confirmation_ts          as timestamp)  as confirmation_ts
from {{ source('agentic_commerce', 'cart') }}
