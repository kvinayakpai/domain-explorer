{{ config(materialized='table') }}

with pe as (select * from {{ ref('stg_revenue_growth_management__price_events') }}),
     a  as (select * from {{ ref('dim_account_rgm') }}),
     p  as (select * from {{ ref('dim_pack') }})

select
    pe.price_event_id,
    cast({{ format_date('cast(pe.effective_from as date)', '%Y%m%d') }} as integer) as date_key,
    a.account_sk,
    p.pack_sk,
    pe.event_type,
    pe.prior_list_price_cents,
    pe.new_list_price_cents,
    pe.price_delta_cents,
    pe.price_delta_pct,
    pe.prior_srp_cents,
    pe.new_srp_cents,
    pe.currency,
    pe.announced_at,
    pe.effective_from,
    pe.source_system,
    pe.approver_role
from pe
left join a on a.account_id = pe.account_id
left join p on p.pack_id    = pe.pack_id
