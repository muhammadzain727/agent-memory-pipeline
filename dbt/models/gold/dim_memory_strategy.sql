
{{ config(
    materialized='table',
    post_hook=[
        "ALTER TABLE {{ this }} ADD CONSTRAINT pk_dim_memory_strategy PRIMARY KEY (memory_strategy_key)"
    ]
) }}

SELECT DISTINCT
    memory_strategy AS memory_strategy_key,
    memory_strategy AS strategy_name

FROM {{ ref('silver_agent_interactions') }}

WHERE memory_strategy IS NOT NULL
