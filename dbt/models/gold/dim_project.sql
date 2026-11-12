
{{ config(
    materialized='table',
    post_hook=[
        "ALTER TABLE {{ this }} ADD CONSTRAINT pk_dim_project PRIMARY KEY (project_key)"
    ]
) }}

SELECT DISTINCT
    project_id AS project_key,
    project_id,
    'Project ' || project_id::TEXT AS project_name

FROM {{ ref('silver_agent_interactions') }}

WHERE project_id IS NOT NULL
