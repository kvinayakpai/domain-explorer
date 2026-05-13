{{ config(materialized='view') }}

select
    cast(rule_id                  as varchar)    as rule_id,
    cast(rule_name                as varchar)    as rule_name,
    cast(priority                 as smallint)   as priority,
    cast(condition_json           as varchar)    as condition_json,
    cast(cost_weight              as double)     as cost_weight,
    cast(speed_weight             as double)     as speed_weight,
    cast(capacity_weight          as double)     as capacity_weight,
    cast(clearance_pull_weight    as double)     as clearance_pull_weight,
    cast(effective_from           as timestamp)  as effective_from,
    cast(effective_to             as timestamp)  as effective_to,
    cast(status                   as varchar)    as status
from {{ source('omnichannel_oms', 'sourcing_rule') }}
