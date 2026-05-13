{{ config(materialized='view') }}

select
    cast(pack_id                    as varchar)  as pack_id,
    cast(sku_id                     as varchar)  as sku_id,
    cast(pack_name                  as varchar)  as pack_name,
    cast(pack_size_count            as smallint) as pack_size_count,
    cast(pack_format                as varchar)  as pack_format,
    cast(ppa_tier                   as varchar)  as ppa_tier,
    cast(ladder_rank                as smallint) as ladder_rank,
    cast(benchmark_net_price_cents  as bigint)   as benchmark_net_price_cents,
    cast(benchmark_margin_cents     as bigint)   as benchmark_margin_cents,
    cast(launch_date                as date)     as launch_date,
    cast(status                     as varchar)  as status
from {{ source('revenue_growth_management', 'pack') }}
