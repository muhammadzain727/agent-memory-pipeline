
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


with DAG(
    dag_id="agent_memory_pipeline",
    description="Agent and Jira ingestion, dbt transformations and quality tests",
    default_args=default_args,
    start_date=datetime(2026, 11, 1),
    schedule="@daily",
    catchup=False,
    params={
        "file_version": Param(
            "v1",
            type="string",
            description="Source file version"
        )
    },
    tags=["data-engineering", "ingestion", "bronze", "dbt", "gold"]
) as dag:

    file_path = "/opt/airflow/data/agent/test_interactions_{{ ds }}.csv"

    generate_data = BashOperator(
        task_id="generate_test_data",
        bash_command=(
            "/opt/dbt-venv/bin/python "
            "/opt/airflow/scripts/airflow_ingestion.py "
            "generate "
            "--run-date '{{ ds }}' "
            "--file-version '{{ params.file_version }}' "
            f"--file-path '{file_path}'"
        )
    )

    validate_data = BashOperator(
        task_id="validate_test_data",
        bash_command=(
            "/opt/dbt-venv/bin/python "
            "/opt/airflow/scripts/airflow_ingestion.py "
            "validate "
            f"--run-date '{{{{ ds }}}}' "
            f"--file-path '{file_path}'"
        )
    )

    load_agent_bronze = BashOperator(
        task_id="load_agent_bronze_data",
        bash_command=(
            "/opt/dbt-venv/bin/python "
            "/opt/airflow/scripts/airflow_ingestion.py "
            "load "
            f"--run-date '{{{{ ds }}}}' "
            f"--file-path '{file_path}'"
        )
    )

    load_jira_bronze = BashOperator(
        task_id="load_jira_bronze_data",
        bash_command=(
            "/opt/dbt-venv/bin/python "
            "/opt/airflow/scripts/ingest_jira.py"
        )
    )

    dbt_run = BashOperator(
        task_id="dbt_transformations",
        bash_command=(
            "/opt/dbt-venv/bin/dbt run "
            "--project-dir /opt/airflow/dbt "
            "--profiles-dir /opt/airflow/dbt"
        )
    )

    create_gold_relationships = BashOperator(
        task_id="create_gold_relationships",
        bash_command=(
            "/opt/dbt-venv/bin/dbt run-operation create_gold_constraints "
            "--project-dir /opt/airflow/dbt "
            "--profiles-dir /opt/airflow/dbt"
        )
    )

    dbt_test = BashOperator(
        task_id="dbt_data_quality_tests",
        bash_command=(
            "/opt/dbt-venv/bin/dbt test "
            "--project-dir /opt/airflow/dbt "
            "--profiles-dir /opt/airflow/dbt"
        )
    )

    generate_data >> validate_data >> load_agent_bronze

    [load_agent_bronze, load_jira_bronze] >> dbt_run

    dbt_run >> create_gold_relationships >> dbt_test
