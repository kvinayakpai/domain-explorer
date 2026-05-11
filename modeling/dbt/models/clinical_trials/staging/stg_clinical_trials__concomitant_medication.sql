-- Staging: SDTM CM (Concomitant Medications).
{{ config(materialized='view') }}

select
    cast(cmseq    as bigint)  as cmseq,
    cast(usubjid  as varchar) as usubjid,
    cast(cmtrt    as varchar) as cmtrt,
    cast(cmindc   as varchar) as cmindc,
    cast(cmdose   as double)  as cmdose,
    cast(cmdosu   as varchar) as cmdosu,
    cast(cmdosfrq as varchar) as cmdosfrq,
    cast(cmroute  as varchar) as cmroute,
    cast(cmstdtc  as date)    as cmstdtc,
    cast(cmendtc  as date)    as cmendtc
from {{ source('clinical_trials', 'concomitant_medication') }}
