
import json
import os
from pathlib import Path

from db_connection import get_connection
from psycopg2.extras import Json, execute_values


DATA_FILE = Path(
    "/opt/airflow/data/jira/extracted/apache_issues_10000.jsonl"
)


def get_value(record, *keys):
    """Return the first available nonempty field."""
    for key in keys:
        value = record.get(key)
        if value is not None:
            return value
    return None


def load_jira_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"File not found: {DATA_FILE}")

    records = []

    with DATA_FILE.open("r", encoding="utf-16") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                )

            if not isinstance(record, dict):
                raise ValueError(
                    f"Expected a JSON object on line {line_number}"
                )

            issue_id = get_value(record, "id")

            if issue_id is None:
                raise ValueError(
                    f"Missing issue ID on line {line_number}"
                )

            records.append((
                str(issue_id),
                get_value(record, "key"),
                get_value(record, "project", "projectKey"),
                get_value(record, "issuetype", "issueType"),
                get_value(record, "status"),
                get_value(record, "priority"),
                get_value(record, "created"),
                get_value(record, "updated"),
                get_value(record.get("fields", {}), "summary"),
                Json(record)
            ))

    if not records:
        raise ValueError("No Jira records found")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bronze.jira_issues_raw (
                    issue_id TEXT PRIMARY KEY,
                    issue_key TEXT,
                    project_info JSONB,
                    issue_type JSONB,
                    status_info JSONB,
                    priority_info JSONB,
                    created_at_source TEXT,
                    updated_at_source TEXT,
                    summary TEXT,
                    raw_payload JSONB NOT NULL,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            execute_values(
                cursor,
                """
                INSERT INTO bronze.jira_issues_raw (
                    issue_id,
                    issue_key,
                    project_info,
                    issue_type,
                    status_info,
                    priority_info,
                    created_at_source,
                    updated_at_source,
                    summary,
                    raw_payload
                )
                VALUES %s
                ON CONFLICT (issue_id)
                DO UPDATE SET
                    issue_key = EXCLUDED.issue_key,
                    project_info = EXCLUDED.project_info,
                    issue_type = EXCLUDED.issue_type,
                    status_info = EXCLUDED.status_info,
                    priority_info = EXCLUDED.priority_info,
                    created_at_source = EXCLUDED.created_at_source,
                    updated_at_source = EXCLUDED.updated_at_source,
                    summary = EXCLUDED.summary,
                    raw_payload = EXCLUDED.raw_payload,
                    ingested_at = CURRENT_TIMESTAMP;
                """,
                records,
                page_size=1000
            )

            cursor.execute("""
                SELECT COUNT(*)
                FROM bronze.jira_issues_raw;
            """)

            total_rows = cursor.fetchone()[0]

        connection.commit()

        print("JIRA INGESTION SUCCESSFUL")
        print(f"Records processed: {len(records)}")
        print(f"Total records in Bronze: {total_rows}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    load_jira_data()
