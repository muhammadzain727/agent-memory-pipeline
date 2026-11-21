from datetime import datetime, timedelta

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2)
}

PYTHON = "/opt/dbt-venv/bin/python"
SCRIPTS = "/opt/airflow/scripts"
DBT_ARGS = "--project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt"

# The version is part of the file name, so a new version is a new file:
# file_version=v1 reads agent_conversations_v1.json.
AGENT_FILE = (
    "/opt/airflow/data/agent/agent_conversations_{{ params.file_version }}.json"
)

JIRA_FILE = "/opt/airflow/data/jira/extracted/apache_issues_10000.jsonl"


with DAG(
    dag_id="agent_memory_pipeline",
    description="Agent and Jira ingestion, dbt transformations and quality tests",
    doc_md="""
### Agent memory pipeline

1. `generate_agent_data` creates the synthetic Agent interactions (fixed seed).
2. `validate_agent_data` checks the file before anything is loaded.
3. `load_agent_bronze_data` and `load_jira_bronze_data` upsert into bronze
   and write one row each to `audit.pipeline_runs`.
4. `dbt_transformations` builds staging, silver and gold.
5. `create_gold_relationships` adds primary and foreign keys to gold.
6. `dbt_data_quality_tests` runs the dbt tests.

Parameter `file_version` (default `v1`) selects the Agent source file and is
stored in bronze. Every load is an upsert, so a re-run creates no duplicates.
""",
    default_args=default_args,
    start_date=datetime(2026, 11, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    params={
        "file_version": Param(
            "v1",
            type="string",
            description="Source file version"
        )
    },
    tags=["data-engineering", "ingestion", "bronze", "dbt", "gold"]
) as dag:

    generate_agent_data = BashOperator(
        task_id="generate_agent_data",
        bash_command=(
            f"{PYTHON} {SCRIPTS}/generate_synthetic_data.py "
            "--output '" + AGENT_FILE + "'"
        )
    )

    validate_agent_data = BashOperator(
        task_id="validate_agent_data",
        bash_command=(
            f"{PYTHON} {SCRIPTS}/ingest_agent.py validate "
            "--file-path '" + AGENT_FILE + "'"
        )
    )

    load_agent_bronze = BashOperator(
        task_id="load_agent_bronze_data",
        bash_command=(
            f"{PYTHON} {SCRIPTS}/ingest_agent.py load "
            "--file-path '" + AGENT_FILE + "' "
            "--file-version '{{ params.file_version }}' "
            "--run-date '{{ ds }}'"
        )
    )

    load_jira_bronze = BashOperator(
        task_id="load_jira_bronze_data",
        bash_command=(
            f"{PYTHON} {SCRIPTS}/ingest_jira.py "
            "--file-path '" + JIRA_FILE + "' "
            "--file-version '{{ params.file_version }}' "
            "--run-date '{{ ds }}'"
        )
    )

    dbt_run = BashOperator(
        task_id="dbt_transformations",
        bash_command=f"/opt/dbt-venv/bin/dbt run {DBT_ARGS}"
    )

    create_gold_relationships = BashOperator(
        task_id="create_gold_relationships",
        bash_command=(
            "/opt/dbt-venv/bin/dbt run-operation create_gold_constraints "
            + DBT_ARGS
        )
    )

    dbt_test = BashOperator(
        task_id="dbt_data_quality_tests",
        bash_command=f"/opt/dbt-venv/bin/dbt test {DBT_ARGS}"
    )

    generate_agent_data >> validate_agent_data >> load_agent_bronze

    [load_agent_bronze, load_jira_bronze] >> dbt_run

    dbt_run >> create_gold_relationships >> dbt_test
