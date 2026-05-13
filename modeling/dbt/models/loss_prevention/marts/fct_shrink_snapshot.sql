-- Fact: store × department × month shrink snapshot. The ledger truth that
-- exceptions and incidents are reconciled against post-physical-count.
{{ config(materialized='table') }}

with x as (select * from {{ ref('stg_loss_prevention__shrink_snapshot') }}),
     s as (select * from {{ ref('dim_store_lp') }})

select
    x.snapshot_id,
    cast({{ format_date('cast(x.period_start as date)', '%Y%m%d') }} as integer) as date_key,
    s.store_sk,
    x.department,
    x.period_start,
    x.period_end,
    x.opening_inventory_minor,
    x.receipts_minor,
    x.cogs_minor,
    x.closing_inventory_minor,
    x.known_shrink_minor,
    x.unknown_shrink_minor,
    x.total_shrink_minor,
    x.shrink_pct
from x
left join s on s.store_id = x.store_id
