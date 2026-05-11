-- Staging: SDTM SV (Subject Visits).
{{ config(materialized='view') }}

select
    cast(usubjid    as varchar) as usubjid,
    cast(visit      as varchar) as visit,
    cast(visitnum   as integer) as visitnum,
    cast(svstdtc    as date)    as svstdtc,
    cast(svendtc    as date)    as svendtc,
    cast(svstatus   as varchar) as svstatus,
    md5(usubjid || '|' || cast(visitnum as varchar)) as visit_bk
from {{ source('clinical_trials', 'visit') }}
