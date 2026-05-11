-- Grain: one row per case-level reaction (PV adverse event).
{{ config(materialized='table') }}

with ae as (select * from {{ ref('stg_pharmacovigilance__adverse_events') }}),
     c as (select * from {{ ref('stg_pharmacovigilance__cases') }})

select
    ae.ae_id                                            as ae_id,
    md5(ae.case_id)                                     as case_key,
    md5(c.patient_id)                                   as patient_key,
    md5(c.primary_product_id)                           as primary_product_key,
    cast({{ format_date('ae.onset_date', '%Y%m%d') }} as integer)  as onset_date_key,
    ae.meddra_pt,
    ae.outcome,
    ae.is_fatal,
    ae.onset_date,
    c.seriousness,
    c.expectedness
from ae
left join c on c.case_id = ae.case_id
