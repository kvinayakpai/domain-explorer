-- Data Vault hub: one row per physical pump (maker's serial).
select
    md5(equipment_id)                     as hk_equipment,
    equipment_id,
    current_timestamp                     as load_dts,
    'SAP_PM'                              as record_source
from {{ ref('stg_refinery_operations__equipment') }}
