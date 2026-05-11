-- Staging: SDTM DM (Demographics).
{{ config(materialized='view') }}

select
    cast(usubjid   as varchar) as usubjid,
    cast(studyid   as varchar) as studyid,
    cast(siteid    as varchar) as siteid,
    cast(subjid    as varchar) as subjid,
    cast(rfstdtc   as date)    as rfstdtc,
    cast(rfendtc   as date)    as rfendtc,
    cast(rficdtc   as date)    as rficdtc,
    cast(armcd     as varchar) as armcd,
    cast(actarmcd  as varchar) as actarmcd,
    cast(age       as integer) as age,
    cast(ageu      as varchar) as ageu,
    cast(sex       as varchar) as sex,
    cast(race      as varchar) as race,
    cast(ethnic    as varchar) as ethnic,
    cast(country   as varchar) as country,
    cast(dthfl     as varchar) as dthfl,
    case
        when cast(age as integer) < 30 then '18-29'
        when cast(age as integer) < 50 then '30-49'
        when cast(age as integer) < 65 then '50-64'
        when cast(age as integer) < 80 then '65-79'
        else '80+'
    end as age_band
from {{ source('clinical_trials', 'subject') }}
