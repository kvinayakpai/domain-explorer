-- DSP dimension distilled from bid responses.
{{ config(materialized='table') }}

with ids as (
    select distinct dsp_id from {{ ref('stg_programmatic_advertising__bid_response') }}
    where dsp_id is not null
)

select
    md5(dsp_id)            as dsp_key,
    dsp_id,
    'DSP ' || dsp_id       as dsp_name,
    true                   as is_current
from ids
