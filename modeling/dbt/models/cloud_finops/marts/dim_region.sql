-- Region catalog dimension.
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_cloud_finops__region') }})

select
    md5(provider || '|' || region_id) as region_key,
    region_id,
    provider,
    geography
from r
