-- Product dimension distilled from work-order product codes.
-- Suffixed name avoids collision with merchandising/dim_product.
{{ config(materialized='table') }}

with codes as (
    select distinct product_code from {{ ref('stg_mes_quality__work_orders') }}
    where product_code is not null
)

select
    md5(product_code)            as product_key,
    product_code                 as product_id,
    'Product ' || product_code   as product_name,
    'A'                          as revision,
    true                         as is_current
from codes
