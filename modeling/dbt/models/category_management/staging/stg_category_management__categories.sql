{{ config(materialized='view') }}

select
    cast(category_id        as varchar)    as category_id,
    cast(category_name      as varchar)    as category_name,
    cast(parent_category_id as varchar)    as parent_category_id,
    cast(category_level     as varchar)    as category_level,
    cast(category_role      as varchar)    as category_role,
    cast(linear_ft_target   as double)     as linear_ft_target,
    cast(gpc_brick          as varchar)    as gpc_brick,
    cast(status             as varchar)    as status,
    cast(created_at         as timestamp)  as created_at
from {{ source('category_management', 'category') }}
