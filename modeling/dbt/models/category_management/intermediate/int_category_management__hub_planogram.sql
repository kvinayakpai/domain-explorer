-- Vault hub for the Planogram business key.
{{ config(materialized='ephemeral') }}

with src as (
    select planogram_id
    from {{ ref('stg_category_management__planograms') }}
    where planogram_id is not null
)

select
    md5(planogram_id)                  as h_planogram_hk,
    planogram_id                       as planogram_bk,
    current_date                       as load_date,
    'category_management.planogram'    as record_source
from src
group by planogram_id
