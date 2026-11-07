-- Data Vault link: a pump installed in a position. Effectivity dates are kept with
-- the link here for convenience; in the vault DDL they live in a satellite.
select
    md5(i.installation_id)                as hk_installation,
    md5(i.functional_location_id)         as hk_functional_location,
    md5(i.equipment_id)                   as hk_equipment,
    i.installation_id,
    i.installed_from,
    i.installed_to,
    current_timestamp                     as load_dts,
    'SAP_PM'                              as record_source
from {{ ref('stg_refinery_operations__installation') }} i
