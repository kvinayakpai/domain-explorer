-- Vault hub for Line.
{{ config(materialized='ephemeral') }}

with src as (
    select line_id from {{ ref('stg_mes_quality__lines') }}
    where line_id is not null
)

select
    md5(line_id)            as h_line_hk,
    line_id                 as line_bk,
    current_date            as load_date,
    'mes_quality.lines'     as record_source
from src
group by line_id
