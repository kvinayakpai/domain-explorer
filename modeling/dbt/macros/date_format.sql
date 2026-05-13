{# format_date(col, fmt)

   Cross-DB date/timestamp formatting.

   Callers pass DuckDB / strftime-style format codes as a *plain Jinja string*
   (no surrounding SQL quotes), e.g.:

       {{ format_date('date_day', '%Y%m%d') }}

   On DuckDB this dispatches to `strftime(col, '<fmt>')`. On Postgres (the
   default) it translates the strftime tokens into the equivalent `to_char`
   pattern and emits `to_char(col, '<translated>')`.

   Token mapping (DuckDB strftime  ->  Postgres to_char):
       %Y -> YYYY      4-digit year
       %y -> YY        2-digit year
       %m -> MM        zero-padded month number
       %d -> DD        zero-padded day-of-month
       %H -> HH24      24-hour
       %I -> HH12      12-hour
       %M -> MI        minutes
       %S -> SS        seconds
       %A -> FMDay     full weekday name (FM trims trailing spaces)
       %a -> FMDy      abbreviated weekday name
       %B -> FMMonth   full month name
       %b -> FMMon     abbreviated month name
       %j -> DDD       day-of-year
       %V -> IW        ISO week number
       %u -> ID        ISO day-of-week (1=Mon..7=Sun)

   Order of replacements matters only for substrings; the table above has no
   internal ambiguity since every strftime token starts with `%` while no
   to_char token does.

   Edge cases: literal `%%` is not handled. ISO-week formatting using `%Y` is
   technically misleading at year boundaries (use `IYYY` for strict ISO-year
   on Postgres) — none of the call sites in this repo hit that case.
#}
{% macro format_date(col, fmt) %}
  {{ return(adapter.dispatch('format_date')(col, fmt)) }}
{% endmacro %}

{% macro default__format_date(col, fmt) %}
  {%- set pg_fmt = fmt
        | replace('%Y', 'YYYY')
        | replace('%y', 'YY')
        | replace('%m', 'MM')
        | replace('%d', 'DD')
        | replace('%H', 'HH24')
        | replace('%I', 'HH12')
        | replace('%M', 'MI')
        | replace('%S', 'SS')
        | replace('%A', 'FMDay')
        | replace('%a', 'FMDy')
        | replace('%B', 'FMMonth')
        | replace('%b', 'FMMon')
        | replace('%j', 'DDD')
        | replace('%V', 'IW')
        | replace('%u', 'ID')
  -%}
  to_char({{ col }}, '{{ pg_fmt }}')
{% endmacro %}

{% macro postgres__format_date(col, fmt) %}
  {{ return(default__format_date(col, fmt)) }}
{% endmacro %}

{% macro duckdb__format_date(col, fmt) %}
  strftime({{ col }}, '{{ fmt }}')
{% endmacro %}
