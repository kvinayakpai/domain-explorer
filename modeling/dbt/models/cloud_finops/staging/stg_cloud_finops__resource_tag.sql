{{ config(materialized='view') }}

select
    cast(tag_id      as varchar)   as tag_id,
    cast(resource_id as varchar)   as resource_id,
    cast(tag_key     as varchar)   as tag_key,
    cast(tag_value   as varchar)   as tag_value,
    cast(tagged_at   as timestamp) as tagged_at
from {{ source('cloud_finops', 'resource_tag') }}
