-- Vault hub for the Segment business key.
{{ config(materialized='ephemeral') }}

with src as (
    select segment_id
    from {{ ref('stg_customer_loyalty_cdp__segment') }}
    where segment_id is not null
)

select
    md5(segment_id)                                   as h_segment_hk,
    segment_id                                        as segment_bk,
    current_date                                      as load_date,
    'customer_loyalty_cdp.segment'                    as record_source
from src
group by segment_id
