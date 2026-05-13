{{ config(materialized='view') }}

select
    cast(epod_id              as varchar)  as epod_id,
    cast(stop_id              as varchar)  as stop_id,
    cast(order_id             as varchar)  as order_id,
    cast(signed_at            as timestamp) as signed_at,
    cast(signed_by            as varchar)  as signed_by,
    cast(signature_image_uri  as varchar)  as signature_image_uri,
    cast(photo_uri            as varchar)  as photo_uri,
    cast(geo_lat              as double)   as geo_lat,
    cast(geo_lng              as double)   as geo_lng,
    cast(device_id            as varchar)  as device_id,
    cast(edi_895_doc_id       as varchar)  as edi_895_doc_id
from {{ source('direct_store_delivery', 'epod_event') }}
