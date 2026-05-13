-- Vault hub for the Savings Event business key.
{{ config(materialized='ephemeral') }}

select
    md5(savings_event_id)                                as h_savings_event_hk,
    savings_event_id                                     as savings_event_bk,
    current_date                                         as load_date,
    'procurement_spend_analytics.savings_event'          as record_source
from {{ ref('stg_procurement_spend_analytics__savings_event') }}
where savings_event_id is not null
group by savings_event_id
