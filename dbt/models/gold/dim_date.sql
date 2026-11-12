
{{ config(
    materialized='table',
    post_hook=[
        "ALTER TABLE {{ this }} ADD CONSTRAINT pk_dim_date PRIMARY KEY (date_key)"
    ]
) }}

SELECT DISTINCT
    CAST(interaction_time AS DATE) AS date_key,
    EXTRACT(YEAR FROM interaction_time)::INTEGER AS year,
    EXTRACT(MONTH FROM interaction_time)::INTEGER AS month,
    EXTRACT(DAY FROM interaction_time)::INTEGER AS day,
    TO_CHAR(interaction_time, 'Month') AS month_name,
    TO_CHAR(interaction_time, 'Day') AS day_name

FROM {{ ref('silver_agent_interactions') }}

WHERE interaction_time IS NOT NULL
