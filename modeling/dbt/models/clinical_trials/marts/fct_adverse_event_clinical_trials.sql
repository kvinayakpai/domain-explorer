-- Grain: one row per SDTM adverse event.
{{ config(materialized='table') }}

with ae as (select * from {{ ref('stg_clinical_trials__adverse_event') }}),
     hub_s as (select * from {{ ref('int_clinical_trials__hub_subject') }}),
     lnk as (select * from {{ ref('int_clinical_trials__link_subject_site') }})

select
    ae.aeseq                                            as ae_id,
    md5(cast(ae.aeseq as varchar))                      as ae_key,
    hub_s.h_subject_hk                                  as subject_key,
    lnk.h_study_hk                                      as study_key,
    lnk.h_site_hk                                       as site_key,
    cast({{ format_date('ae.aestdtc', '%Y%m%d') }} as integer)     as onset_date_key,
    cast({{ format_date('ae.aeendtc', '%Y%m%d') }} as integer)     as end_date_key,
    ae.aeterm,
    ae.aedecod,
    ae.aebodsys,
    ae.aesev,
    ae.aerel,
    ae.aeacn,
    ae.aeout,
    ae.is_serious,
    ae.is_related,
    ae.aestdtc                                          as onset_ts,
    ae.aeendtc                                          as end_ts,
    case
        when ae.aeendtc is not null
            then {{ dbt_utils.datediff('ae.aestdtc', 'ae.aeendtc', 'day') }}
    end                                                 as duration_days
from ae
left join hub_s on hub_s.subject_bk    = ae.usubjid
left join lnk   on lnk.h_subject_hk    = hub_s.h_subject_hk
