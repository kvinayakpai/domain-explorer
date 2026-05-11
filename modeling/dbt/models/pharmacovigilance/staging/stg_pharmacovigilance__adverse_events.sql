-- Staging: case-level adverse event reactions (PV).
{{ config(materialized='view') }}

select
    cast(ae_id      as varchar) as ae_id,
    cast(case_id    as varchar) as case_id,
    cast(meddra_pt  as varchar) as meddra_pt,
    cast(outcome    as varchar) as outcome,
    cast(onset_date as date)    as onset_date,
    case when cast(outcome as varchar) = 'fatal' then true else false end as is_fatal
from {{ source('pharmacovigilance', 'adverse_events') }}
