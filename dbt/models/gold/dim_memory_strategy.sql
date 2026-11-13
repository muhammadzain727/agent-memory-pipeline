
{{ config(materialized='table') }}

SELECT DISTINCT
    memory_strategy AS memory_strategy_key,
    memory_strategy AS strategy_name

FROM {{ ref('silver_agent_interactions') }}

WHERE memory_strategy IS NOT NULL
