{{ config(materialized='view') }}

select
    cast(po_id                   as varchar)    as po_id,
    cast(po_number               as varchar)    as po_number,
    cast(supplier_id             as varchar)    as supplier_id,
    cast(contract_id             as varchar)    as contract_id,
    cast(requester_user_id       as varchar)    as requester_user_id,
    cast(buyer_user_id           as varchar)    as buyer_user_id,
    cast(cost_center             as varchar)    as cost_center,
    cast(gl_account              as varchar)    as gl_account,
    cast(legal_entity            as varchar)    as legal_entity,
    cast(plant_id                as varchar)    as plant_id,
    cast(requisition_id          as varchar)    as requisition_id,
    cast(requisition_ts          as timestamp)  as requisition_ts,
    cast(po_issued_ts            as timestamp)  as po_issued_ts,
    cast(buying_channel          as varchar)    as buying_channel,
    cast(total_amount            as double)     as total_amount,
    cast(total_currency          as varchar)    as total_currency,
    cast(total_amount_base_usd   as double)     as total_amount_base_usd,
    cast(payment_terms           as varchar)    as payment_terms,
    cast(incoterms               as varchar)    as incoterms,
    cast(status                  as varchar)    as status,
    cast(touchless               as boolean)    as touchless,
    cast(maverick_flag           as boolean)    as maverick_flag,
    cast(edi_855_received        as boolean)    as edi_855_received,
    cast(category_code           as varchar)    as category_code,
    case
        when requisition_ts is not null and po_issued_ts is not null
            then ({{ dbt_utils.datediff('requisition_ts', 'po_issued_ts', 'minute') }} / 60.0)
    end as cycle_time_hours,
    case when contract_id is not null then true else false end as has_contract
from {{ source('procurement_spend_analytics', 'purchase_order') }}
