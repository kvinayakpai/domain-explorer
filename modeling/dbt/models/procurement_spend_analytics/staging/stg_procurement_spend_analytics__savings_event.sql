{{ config(materialized='view') }}

select
    cast(savings_event_id      as varchar)    as savings_event_id,
    cast(supplier_id           as varchar)    as supplier_id,
    cast(contract_id           as varchar)    as contract_id,
    cast(category_code         as varchar)    as category_code,
    cast(event_type            as varchar)    as event_type,
    cast(savings_kind          as varchar)    as savings_kind,
    cast(committed_amount_usd  as double)     as committed_amount_usd,
    cast(realized_amount_usd   as double)     as realized_amount_usd,
    cast(baseline_method       as varchar)    as baseline_method,
    cast(signed_off_by         as varchar)    as signed_off_by,
    cast(committed_at          as timestamp)  as committed_at,
    cast(realized_through_ts   as timestamp)  as realized_through_ts,
    case
        when committed_amount_usd > 0
            then realized_amount_usd / committed_amount_usd
        else 0
    end as realization_pct
from {{ source('procurement_spend_analytics', 'savings_event') }}
