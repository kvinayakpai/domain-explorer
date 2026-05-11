-- Staging: SDTM EG (ECG Test Results).
{{ config(materialized='view') }}

select
    cast(egseq    as bigint)  as egseq,
    cast(usubjid  as varchar) as usubjid,
    cast(egtestcd as varchar) as egtestcd,
    cast(egorres  as double)  as egorres,
    cast(egorresu as varchar) as egorresu,
    cast(egstresn as double)  as egstresn,
    cast(egnrind  as varchar) as egnrind,
    cast(egdtc    as date)    as egdtc
from {{ source('clinical_trials', 'ecg') }}
