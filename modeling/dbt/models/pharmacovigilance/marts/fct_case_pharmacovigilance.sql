-- Grain: one row per ICSR case, with FKs to product/patient and aggregate AE/follow-up counts.
{{ config(materialized='table') }}

with sat as (select * from {{ ref('int_pharmacovigilance__sat_case') }}),
     hub as (select * from {{ ref('int_pharmacovigilance__hub_case') }}),
     c as (select * from {{ ref('stg_pharmacovigilance__cases') }}),
     ae as (
        select case_id, count(*) as ae_count, max(case when is_fatal then 1 else 0 end) as has_fatal
        from {{ ref('stg_pharmacovigilance__adverse_events') }}
        group by case_id
     ),
     fu as (
        select case_id, count(*) as followup_count
        from {{ ref('stg_pharmacovigilance__follow_ups') }}
        group by case_id
     )

select
    h.h_case_hk                                          as case_key,
    h.case_bk                                            as case_id,
    cast({{ format_date('c.received_at', '%Y%m%d') }} as integer)   as received_date_key,
    c.received_at                                        as received_ts,
    md5(c.patient_id)                                    as patient_key,
    md5(c.primary_product_id)                            as primary_product_key,
    md5(c.reporter_id)                                   as reporter_key,
    s.seriousness,
    s.expectedness,
    s.case_status,
    s.country,
    s.is_serious,
    coalesce(ae.ae_count, 0)                             as ae_count,
    case when coalesce(ae.has_fatal, 0) = 1 then true else false end as has_fatal_outcome,
    coalesce(fu.followup_count, 0)                       as followup_count
from hub h
join sat s on s.h_case_hk = h.h_case_hk
join c    on c.case_id    = h.case_bk
left join ae on ae.case_id = h.case_bk
left join fu on fu.case_id = h.case_bk
