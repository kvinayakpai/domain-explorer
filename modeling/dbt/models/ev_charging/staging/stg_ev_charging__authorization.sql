{{ config(materialized='view') }}

select
    cast(authorization_id as varchar)   as authorization_id,
    cast(id_token         as varchar)   as id_token,
    cast(id_token_type    as varchar)   as id_token_type,
    cast(requested_at     as timestamp) as requested_at,
    cast(decision         as varchar)   as decision,
    cast(emsp_id          as varchar)   as emsp_id,
    upper(country_code)                 as country_code,
    cast({{ format_date('requested_at', '%Y%m%d') }} as integer) as requested_date_key
from {{ source('ev_charging', 'authorization') }}
