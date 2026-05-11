-- Staging: signal-detection events.
{{ config(materialized='view') }}

select
    cast(signal_id   as varchar)   as signal_id,
    cast(product_id  as varchar)   as product_id,
    cast(meddra_pt   as varchar)   as meddra_pt,
    cast(detected_at as timestamp) as detected_at,
    cast(method      as varchar)   as method,
    cast(status      as varchar)   as status
from {{ source('pharmacovigilance', 'signals') }}
