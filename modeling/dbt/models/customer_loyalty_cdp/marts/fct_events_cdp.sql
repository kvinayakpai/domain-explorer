-- Fact — one row per behavioral / engagement event.
{{ config(materialized='table') }}

with e as (select * from {{ ref('stg_customer_loyalty_cdp__event') }}),
     c as (select * from {{ ref('dim_customer_cdp') }}),
     ch as (select * from {{ ref('dim_channel') }})

select
    e.event_id,
    cast({{ format_date('e.event_ts', '%Y%m%d') }} as integer) as date_key,
    c.customer_sk,
    ch.channel_sk,
    e.event_type,
    e.source_system,
    e.campaign_id,
    e.journey_id,
    e.product_id,
    e.order_id,
    e.amount_minor,
    e.currency,
    case e.currency
        when 'USD' then e.amount_minor / 100.0
        when 'EUR' then e.amount_minor / 100.0 * 1.08
        when 'GBP' then e.amount_minor / 100.0 * 1.27
        when 'JPY' then e.amount_minor / 100.0 * 0.0067
        when 'CAD' then e.amount_minor / 100.0 * 0.74
        when 'AUD' then e.amount_minor / 100.0 * 0.66
        else e.amount_minor / 100.0
    end                                                       as amount_usd,
    case when e.event_type = 'purchase' then true else false end                                       as is_purchase,
    case when e.event_type in ('email_open','email_click','push_open','app_open','review_submit')
         then true else false end                                                                       as is_engagement,
    case when e.event_type in ('email_send','push_send','sms_send') then true else false end           as is_marketing_send,
    e.event_ts,
    e.ingest_lag_seconds
from e
left join c  on c.customer_id   = e.customer_id
left join ch on ch.channel_code = e.channel
