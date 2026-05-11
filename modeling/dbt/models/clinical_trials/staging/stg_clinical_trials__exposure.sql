-- Staging: SDTM EX (Exposure / IP administrations).
{{ config(materialized='view') }}

select
    cast(exseq    as bigint)  as exseq,
    cast(usubjid  as varchar) as usubjid,
    cast(extrt    as varchar) as extrt,
    cast(exdose   as double)  as exdose,
    cast(exdosu   as varchar) as exdosu,
    cast(exdosfrq as varchar) as exdosfrq,
    cast(exroute  as varchar) as exroute,
    cast(exstdtc  as date)    as exstdtc,
    cast(exendtc  as date)    as exendtc
from {{ source('clinical_trials', 'exposure') }}
