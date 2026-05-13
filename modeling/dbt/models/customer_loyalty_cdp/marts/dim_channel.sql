-- Channel dimension. Hand-curated; tags owned vs paid.
{{ config(materialized='table') }}

with channel_universe as (
    select 'web'         as channel_code, true  as is_owned, false as is_paid
    union all select 'app',         true,  false
    union all select 'email',       true,  false
    union all select 'push',        true,  false
    union all select 'sms',         true,  false
    union all select 'in_store',    true,  false
    union all select 'call_center', true,  false
    union all select 'chat',        true,  false
    union all select 'paid_media',  false, true
)

select
    cast(row_number() over (order by channel_code) as smallint)  as channel_sk,
    channel_code,
    is_owned,
    is_paid
from channel_universe
