{#
   Use the model's custom schema config verbatim instead of prefixing it
   with the target schema. This gives us clean `bronze`, `silver`, `gold`
   schemas that match the medallion architecture, rather than
   `staging_silver`, `staging_gold`, etc.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
