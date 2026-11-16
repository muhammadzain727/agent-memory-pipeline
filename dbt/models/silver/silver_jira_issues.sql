SELECT
    issue_id,
    issue_key,
    project_key,
    project_name,
    issue_type,
    status,
    priority,
    created_at,
    updated_at,
    summary,
    description,
    ingested_at

FROM {{ ref('stg_jira_issues') }}

WHERE issue_id IS NOT NULL
  AND issue_key IS NOT NULL
  AND project_key IS NOT NULL