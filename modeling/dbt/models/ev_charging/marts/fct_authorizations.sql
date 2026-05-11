-- Grain: one row per Authorize request (RFID / ISO15118 / eMAID).
{{ config(materialized='table') }}

with a as (select * from {{ ref('stg_ev_charging__authorization') }})

select
    md5(a.authorization_id)        as authorization_key,
    a.authorization_id,
    a.id_token,
    a.id_token_type,
    a.requested_at,
    a.requested_date_key,
    a.decision,
    a.emsp_id,
    a.country_code,
    case when a.decision = 'Accepted' then true else false end as is_accepted
from a
