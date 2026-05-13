{{ config(materialized='view') }}

select
    cast(receipt_id           as varchar)    as receipt_id,
    cast(po_id                as varchar)    as po_id,
    cast(po_line_id           as varchar)    as po_line_id,
    cast(receipt_ts           as timestamp)  as receipt_ts,
    cast(quantity_received    as double)     as quantity_received,
    cast(receiver_user_id     as varchar)    as receiver_user_id,
    cast(plant_id             as varchar)    as plant_id,
    cast(gr_document_no       as varchar)    as gr_document_no,
    cast(status               as varchar)    as status
from {{ source('procurement_spend_analytics', 'receipt') }}
