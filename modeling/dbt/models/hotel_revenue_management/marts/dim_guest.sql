-- Guest dimension keyed by md5(guest_id). Surfaces loyalty + region context.
{{ config(materialized='table') }}

with g as (select * from {{ ref('stg_hotel_revenue_management__guests') }})

select
    md5(g.guest_id)                                  as guest_key,
    g.guest_id,
    g.guest_name,
    g.country_code,
    g.loyalty_tier,
    case
        when g.loyalty_tier is null                                          then 'none'
        when upper(g.loyalty_tier) in ('PLATINUM','DIAMOND','TOP_TIER')      then 'top'
        when upper(g.loyalty_tier) in ('GOLD','PREMIUM')                     then 'mid_high'
        when upper(g.loyalty_tier) in ('SILVER','PLUS')                      then 'mid'
        when upper(g.loyalty_tier) in ('BRONZE','BASIC','MEMBER')            then 'low'
        else 'other'
    end                                              as loyalty_band,
    g.lifetime_nights,
    case
        when g.lifetime_nights is null                                       then 'unknown'
        when g.lifetime_nights = 0                                           then 'first_stay'
        when g.lifetime_nights < 5                                           then 'occasional'
        when g.lifetime_nights < 20                                          then 'regular'
        when g.lifetime_nights < 50                                          then 'frequent'
        else 'super_frequent'
    end                                              as stay_band
from g
