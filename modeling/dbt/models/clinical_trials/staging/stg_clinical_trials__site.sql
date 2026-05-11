-- Staging: investigator site master.
{{ config(materialized='view') }}

select
    cast(siteid                  as varchar) as siteid,
    cast(studyid                 as varchar) as studyid,
    cast(site_name               as varchar) as site_name,
    upper(country)                            as country_iso,
    cast(principal_investigator  as varchar) as principal_investigator,
    cast(irb_approval_date       as date)    as irb_approval_date,
    cast(activated_at            as date)    as activated_at,
    cast(subject_target          as integer) as subject_target,
    cast(subject_enrolled        as integer) as subject_enrolled
from {{ source('clinical_trials', 'site') }}
