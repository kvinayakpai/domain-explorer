-- Staging: return events.
{{ config(materialized='view') }}

select
    cast(return_id    as varchar)   as return_id,
    cast(sale_line_id as varchar)   as sale_line_id,
    cast(sku          as varchar)   as sku,
    cast(quantity     as integer)   as quantity,
    cast(amount       as double)    as amount,
    cast(reason       as varchar)   as reason,
    cast(returned_at  as timestamp) as returned_at
from {{ source('merchandising', 'returns') }}
