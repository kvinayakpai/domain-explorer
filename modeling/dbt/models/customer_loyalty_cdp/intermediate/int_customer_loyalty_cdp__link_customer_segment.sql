-- Vault link — customer x segment membership episode.
{{ config(materialized='ephemeral') }}

select
    md5(coalesce(customer_id, '') || '|' || coalesce(segment_id, '') || '|' || cast(entered_at as varchar))  as l_customer_segment_hk,
    md5(customer_id)                                                                                          as h_customer_hk,
    md5(segment_id)                                                                                           as h_segment_hk,
    entered_at,
    exited_at,
    is_current,
    entered_at                                                                                                as load_date,
    'customer_loyalty_cdp.segment_membership'                                                                 as record_source
from {{ ref('stg_customer_loyalty_cdp__segment_membership') }}
where customer_id is not null and segment_id is not null
