-- Service catalog dimension. Surrogate key on (provider, service_name).
{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_cloud_finops__service') }})

select
    md5(provider || '|' || service_name) as service_key,
    service_name,
    provider,
    service_category,
    service_subcategory
from s
