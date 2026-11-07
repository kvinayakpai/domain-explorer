-- Data Vault hub: one row per position business key (SAP PM functional location).
select
    md5(functional_location_id)           as hk_functional_location,
    functional_location_id,
    current_timestamp                     as load_dts,
    'SAP_PM'                              as record_source
from {{ ref('stg_refinery_operations__functional_location') }}
