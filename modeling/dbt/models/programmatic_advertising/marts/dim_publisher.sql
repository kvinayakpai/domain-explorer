-- Publisher dimension distilled from bid requests.
{{ config(materialized='table') }}

with src as (
    select publisher_id, max(site_domain) as site_domain
    from {{ ref('stg_programmatic_advertising__bid_request') }}
    where publisher_id is not null
    group by publisher_id
)

select
    md5(publisher_id)        as publisher_key,
    publisher_id,
    site_domain,
    true                     as is_current
from src
