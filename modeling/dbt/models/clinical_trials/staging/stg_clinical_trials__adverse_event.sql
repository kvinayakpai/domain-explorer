-- Staging: SDTM AE (Adverse Events).
{{ config(materialized='view') }}

select
    cast(aeseq    as bigint)    as aeseq,
    cast(usubjid  as varchar)   as usubjid,
    cast(aeterm   as varchar)   as aeterm,
    cast(aedecod  as varchar)   as aedecod,
    cast(aebodsys as varchar)   as aebodsys,
    cast(aeser    as varchar)   as aeser,
    cast(aesev    as varchar)   as aesev,
    cast(aerel    as varchar)   as aerel,
    cast(aeacn    as varchar)   as aeacn,
    cast(aeout    as varchar)   as aeout,
    cast(aestdtc  as timestamp) as aestdtc,
    cast(aeendtc  as timestamp) as aeendtc,
    case when cast(aeser as varchar) = 'Y' then true else false end as is_serious,
    case
        when cast(aerel as varchar) in ('POSSIBLY RELATED','PROBABLY RELATED','DEFINITELY RELATED')
            then true else false
    end as is_related
from {{ source('clinical_trials', 'adverse_event') }}
