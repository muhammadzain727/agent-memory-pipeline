$sql = @'
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.pipeline_runs (
    run_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dag_id            VARCHAR(150),
    execution_date    TIMESTAMP,
    source_name       VARCHAR(100),
    status            VARCHAR(30),
    records_processed INTEGER,
    records_inserted  INTEGER,
    records_updated   INTEGER,
    error_message     TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.agent_interactions_raw (
    interaction_id          VARCHAR(100) PRIMARY KEY,
    user_id                 INTEGER NOT NULL,
    project_id              INTEGER NOT NULL,
    input_tokens            INTEGER NOT NULL,
    retrieval_latency_ms    NUMERIC(12,2) NOT NULL,
    file_version            VARCHAR(50),
    ingestion_date          DATE NOT NULL,
    raw_payload             JSONB NOT NULL,
    loaded_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_timestamp   TIMESTAMPTZ,
    issue_id                INTEGER,
    user_question           TEXT,
    agent_response          TEXT,
    memory_strategy         TEXT,
    full_history_tokens     INTEGER,
    selected_context_tokens INTEGER,
    retrieved_memory_count  INTEGER,
    response_latency_ms     INTEGER
);

CREATE TABLE IF NOT EXISTS bronze.jira_issues_raw (
    issue_id          TEXT PRIMARY KEY,
    issue_key         TEXT,
    project_info      JSONB,
    issue_type        JSONB,
    status_info       JSONB,
    priority_info     JSONB,
    created_at_source TEXT,
    updated_at_source TEXT,
    summary           TEXT,
    raw_payload       JSONB NOT NULL,
    ingested_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'@
[System.IO.File]::WriteAllText((Join-Path (Get-Location) 'db\init\01_init.sql'), $sql, (New-Object System.Text.UTF8Encoding($false)))
dbq $sql
dbq '\dt bronze.*'