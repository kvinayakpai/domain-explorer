-- Staging: SDTM LB (Laboratory Test Results).
{{ config(materialized='view') }}

select
    cast(lbseq     as bigint)  as lbseq,
    cast(usubjid   as varchar) as usubjid,
    cast(lbtestcd  as varchar) as lbtestcd,
    cast(lbtest    as varchar) as lbtest,
    cast(lbcat     as varchar) as lbcat,
    cast(lborres   as double)  as lborres,
    cast(lborresu  as varchar) as lborresu,
    cast(lbstresn  as double)  as lbstresn,
    cast(lbstresu  as varchar) as lbstresu,
    cast(lbstnrlo  as double)  as lbstnrlo,
    cast(lbstnrhi  as double)  as lbstnrhi,
    cast(lbnrind   as varchar) as lbnrind,
    cast(lbdtc     as date)    as lbdtc,
    cast(visitnum  as integer) as visitnum
from {{ source('clinical_trials', 'lab') }}
