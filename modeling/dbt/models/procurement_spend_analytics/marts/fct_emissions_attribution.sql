-- Fact — Scope 3 Category 1+2 emissions attribution at PO-line grain.
-- The kgco2e_per_usd is the dollar-weighted hybrid factor used at attribution
-- time. Combines factor_source ('primary' | 'activity' | 'spend_based').
{{ config(materialized='table') }}

with l as (select * from {{ ref('stg_procurement_spend_analytics__po_line') }}),
     p as (
        select po_id, supplier_id, po_issued_ts, total_currency
        from {{ ref('stg_procurement_spend_analytics__purchase_order') }}
     ),
     ef as (
        -- Average factor per category as the spend-based fallback.
        select
            category_code,
            avg(factor_kgco2e_per_usd) as avg_factor_kgco2e_per_usd,
            avg(uncertainty_pct)       as avg_uncertainty_pct,
            min(vintage_year)          as min_vintage_year,
            max(ghg_scope3_category)   as scope3_category
        from {{ ref('stg_procurement_spend_analytics__emissions_factor') }}
        group by category_code
     ),
     s as (select supplier_sk, supplier_id from {{ ref('dim_supplier') }}),
     c as (select category_sk, category_code from {{ ref('dim_category_taxonomy') }}),
     cur as (select currency_sk, currency_code from {{ ref('dim_currency') }})

select
    l.po_line_id,
    cast({{ format_date('p.po_issued_ts', '%Y%m%d') }} as integer) as date_key,
    s.supplier_sk,
    c.category_sk,
    cur.currency_sk,
    l.line_amount_base_usd,
    'spend_based'                                          as factor_source,
    ef.min_vintage_year                                    as factor_vintage_year,
    l.scope3_kgco2e,
    case
        when l.line_amount_base_usd > 0
            then cast(l.scope3_kgco2e / l.line_amount_base_usd as double)
        else cast(ef.avg_factor_kgco2e_per_usd as double)
    end                                                    as kgco2e_per_usd,
    cast(ef.avg_uncertainty_pct as double)                 as uncertainty_pct,
    ef.scope3_category
from l
left join p   on p.po_id           = l.po_id
left join ef  on ef.category_code  = l.category_code
left join s   on s.supplier_id     = p.supplier_id
left join c   on c.category_code   = l.category_code
left join cur on cur.currency_code = p.total_currency
