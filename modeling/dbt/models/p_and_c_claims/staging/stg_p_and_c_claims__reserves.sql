-- Staging: reserve postings against the claim header.
{{ config(materialized='view') }}

select
    cast(reserve_id     as varchar)   as reserve_id,
    cast(claim_id       as varchar)   as claim_id,
    cast(reserve_amount as double)    as reserve_amount,
    cast(category       as varchar)   as reserve_category,
    cast(set_at         as timestamp) as set_at
from {{ source('p_and_c_claims', 'reserves') }}
