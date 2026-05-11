-- Vault-style hub for the Site business key.
{{ config(materialized='ephemeral') }}

with src as (
    select siteid, activated_at
    from {{ ref('stg_clinical_trials__site') }}
    where siteid is not null
)

select
    md5(siteid)                              as h_site_hk,
    siteid                                   as site_bk,
    coalesce(min(activated_at), current_date) as load_date,
    'clinical_trials.site'                   as record_source
from src
group by siteid
