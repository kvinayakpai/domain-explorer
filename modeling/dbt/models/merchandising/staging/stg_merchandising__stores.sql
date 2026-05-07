-- Staging: store master.
{{ config(materialized='view') }}

select
    cast(store_id   as varchar) as store_id,
    cast(store_name as varchar) as store_name,
    upper(country)              as country_code,
    cast(region     as varchar) as region,
    cast(format     as varchar) as store_format,
    cast(open_date  as date)    as open_date,
    cast(active     as boolean) as is_active
from {{ source('merchandising', 'stores') }}
