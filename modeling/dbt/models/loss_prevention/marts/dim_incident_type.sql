-- Lookup dimension for incident types with severity tier + NIBRS reportability.
{{ config(materialized='table') }}

with raw as (
    select 1  as incident_type_sk, 'external_shoplift' as incident_type, 'medium' as severity_tier, true  as reportable_nibrs, 'Outside-party theft from sales floor; default to NIBRS 23C/23H.'    as description
    union all select 2,  'internal_theft',    'high',   true,  'Employee theft; sweethearting + cash skim escalate here.'
    union all select 3,  'orc_boost',         'high',   true,  'Organized Retail Crime boost-and-fence; ALTO Alliance reportable.'
    union all select 4,  'burglary',          'high',   true,  'After-hours unlawful entry; NIBRS 220.'
    union all select 5,  'robbery',           'high',   true,  'Threat-of-force theft; NIBRS 120.'
    union all select 6,  'return_abuse',      'low',    false, 'Serial return offender pattern; refund-policy violation.'
    union all select 7,  'refund_fraud',      'medium', true,  'Fraudulent refund (no-receipt, swapped goods).'
    union all select 8,  'cargo_theft',       'high',   true,  'DC / inbound freight loss; FBI cargo theft taskforce reportable.'
)
select * from raw
