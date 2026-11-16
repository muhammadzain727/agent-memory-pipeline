SELECT
    issue_id,
    issue_key,

    raw_payload -> 'fields' -> 'project' ->> 'key' AS project_key,
    raw_payload -> 'fields' -> 'project' ->> 'name' AS project_name,

    issue_type ->> 'name' AS issue_type,
    status_info ->> 'name' AS status,
    priority_info ->> 'name' AS priority,

    created_at_source AS created_at,
    updated_at_source AS updated_at,

    NULLIF(TRIM(summary), '') AS summary,

    raw_payload -> 'fields' ->> 'description' AS description,

    ingested_at

FROM bronze.jira_issues_raw

WHERE issue_id IS NOT NULL