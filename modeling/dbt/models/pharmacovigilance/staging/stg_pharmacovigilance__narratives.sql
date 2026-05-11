-- Staging: case-level narratives.
{{ config(materialized='view') }}

select
    cast(narrative_id  as varchar) as narrative_id,
    cast(case_id       as varchar) as case_id,
    cast(language      as varchar) as language,
    cast(length_words  as integer) as length_words,
    cast(version       as integer) as version
from {{ source('pharmacovigilance', 'narratives') }}
