{{ config(materialized='view') }}

select
    cast(position_id          as varchar)  as position_id,
    cast(planogram_id         as varchar)  as planogram_id,
    cast(sku_id               as varchar)  as sku_id,
    cast(shelf_number         as smallint) as shelf_number,
    cast(position_index       as smallint) as position_index,
    cast(facings              as smallint) as facings,
    cast(facing_depth         as smallint) as facing_depth,
    cast(linear_ft_allocated  as double)   as linear_ft_allocated,
    cast(block_id             as varchar)  as block_id,
    cast(adjacency_left_sku   as varchar)  as adjacency_left_sku,
    cast(adjacency_right_sku  as varchar)  as adjacency_right_sku,
    cast(is_mandated          as boolean)  as is_mandated,
    cast(is_innovation_slot   as boolean)  as is_innovation_slot
from {{ source('category_management', 'planogram_position') }}
