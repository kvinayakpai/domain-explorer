-- Vault satellite carrying mutable Category attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_category_management__categories') }})

select
    md5(category_id)                                                                   as h_category_hk,
    coalesce(created_at, current_timestamp)                                            as load_ts,
    md5(coalesce(category_name,'') || '|' || coalesce(category_level,'') || '|' ||
        coalesce(category_role,'') || '|' || coalesce(status,''))                       as hashdiff,
    category_name,
    parent_category_id,
    category_level,
    category_role,
    linear_ft_target,
    gpc_brick,
    status,
    'category_management.category'                                                      as record_source
from src
