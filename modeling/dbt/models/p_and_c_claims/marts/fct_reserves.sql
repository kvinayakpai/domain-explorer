-- Grain: one row per reserve posting against a claim.
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_p_and_c_claims__reserves') }}),
     hub_c as (select * from {{ ref('int_p_and_c_claims__hub_claim') }}),
     stg_claim as (select * from {{ ref('stg_p_and_c_claims__claims') }})

select
    md5(r.reserve_id)                                  as reserve_key,
    r.reserve_id,
    r.claim_id,
    h.h_claim_hk                                       as claim_key,
    stg_claim.policy_id,
    stg_claim.peril,
    r.reserve_category,
    r.reserve_amount,
    case
        when upper(r.reserve_category) like '%CASE%'    then 'case'
        when upper(r.reserve_category) like '%BULK%'    then 'bulk'
        when upper(r.reserve_category) like '%SALV%'    then 'salvage'
        when upper(r.reserve_category) like '%SUBR%'    then 'subrogation'
        else 'other'
    end                                                 as reserve_category_norm,
    r.set_at,
    cast({{ format_date('r.set_at', '%Y%m%d') }} as integer)       as set_date_key,
    cast(r.set_at as date)                              as set_date
from r
left join hub_c     h on h.claim_bk      = r.claim_id
left join stg_claim   on stg_claim.claim_id = r.claim_id
