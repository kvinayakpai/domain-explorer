-- Staging: markdown / clearance events.
{{ config(materialized='view') }}

select
    cast(markdown_id as varchar)   as markdown_id,
    cast(sku         as varchar)   as sku,
    cast(applied_at  as timestamp) as applied_at,
    cast(depth_pct   as double)    as depth_pct,
    cast(reason      as varchar)   as reason
from {{ source('merchandising', 'markdowns') }}
