-- Small reference dim for the price-event taxonomy.
{{ config(materialized='table') }}

with t as (
    select 'regular'   as price_type, 1::smallint as price_event_type_sk, false as is_promotional, false as is_markdown, 'Standard regular ticketed price (EDI 832/879).' as description
    union all
    select 'promo',     2::smallint, true,  false, 'Promotional price during an active promo (EDI 880/881).'
    union all
    select 'markdown',  3::smallint, false, true,  'Lifecycle markdown driven by sell-through / clearance optimization.'
    union all
    select 'clearance', 4::smallint, false, true,  'Final clearance to clear residual inventory.'
    union all
    select 'cost',      5::smallint, false, false, 'Standard cost from RMS / ERP — used for margin computation.'
)

select
    price_event_type_sk,
    price_type,
    is_promotional,
    is_markdown,
    description
from t
