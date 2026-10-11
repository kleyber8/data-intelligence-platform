{#
    Override del comportamiento por defecto de dbt.

    Por defecto, dbt prefija el custom schema con el schema del target
    (ej: target.schema=silver + custom_schema=silver → silver_silver).

    Este proyecto define explícitamente el schema final en dbt_project.yml
    (+schema: silver, +schema: gold), así que queremos que dbt los use tal cual.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
