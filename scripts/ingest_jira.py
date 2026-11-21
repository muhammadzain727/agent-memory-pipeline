"""Load the Jira issue sample into the bronze layer.

Usage:
    python ingest_jira.py --file-version v1 --run-date 2026-11-16

The load is idempotent: rows are upserted on issue_id, so running it again
never creates duplicates. Each run is recorded in audit.pipeline_runs.
"""

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from psycopg2.extras import Json, execute_values

from db_connection import get_connection
from pipeline_audit import (
    ensure_audit_objects, fail_run, finish_run, start_run
)


DEFAULT_FILE = "/opt/airflow/data/jira/extracted/apache_issues_10000.jsonl"

SOURCE_NAME = "jira_apache_issues"


def pick(record, *names):
    """Return the first non-null value, looking at the top level first and
    then inside the nested "fields" object."""

    fields = record.get("fields")
    sources = [record]

    if isinstance(fields, dict):
        sources.append(fields)

    for name in names:
        for source in sources:
            value = source.get(name)
            if value is not None:
                return value

    return None


def as_json(value):
    """Wrap a value so it is stored in a JSONB column."""
    return None if value is None else Json(value)


def as_text(value):
    return None if value is None else str(value)


def read_records(data_file, file_version):
    """Read the Jira JSON lines file (UTF-16) and build the insert rows."""

    if not data_file.exists():
        raise FileNotFoundError(f"File not found: {data_file}")

    records = []
    seen_ids = set()

    with data_file.open("r", encoding="utf-16") as file:
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

            issue_id = pick(record, "id")

            if issue_id is None:
                raise ValueError(
                    f"Missing issue ID on line {line_number}"
                )

            issue_id = str(issue_id)

            if issue_id in seen_ids:
                raise ValueError(
                    f"Duplicate issue ID {issue_id} on line {line_number}"
                )

            seen_ids.add(issue_id)

            records.append((
                issue_id,
                as_text(pick(record, "key")),
                as_json(pick(record, "project", "projectKey")),
                as_json(pick(record, "issuetype", "issueType")),
                as_json(pick(record, "status")),
                as_json(pick(record, "priority")),
                as_text(pick(record, "created")),
                as_text(pick(record, "updated")),
                as_text(pick(record, "summary")),
                Json(record),
                file_version
            ))

    if not records:
        raise ValueError("No Jira records found")

    return records


def load_jira_data(file_path, file_version, run_date):
    records = read_records(Path(file_path), file_version)

    connection = get_connection()
    run_id = None

    try:
        ensure_audit_objects(connection)
        run_id = start_run(connection, SOURCE_NAME, run_date)

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

            # Added later than the first version of the table
            cursor.execute("""
                ALTER TABLE bronze.jira_issues_raw
                ADD COLUMN IF NOT EXISTS file_version VARCHAR(50);
            """)

            cursor.execute("""
                SELECT COUNT(*)
                FROM bronze.jira_issues_raw
                WHERE issue_id = ANY(%s);
            """, ([row[0] for row in records],))
            updated = cursor.fetchone()[0]
            inserted = len(records) - updated

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
                    raw_payload,
                    file_version
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
                    file_version = EXCLUDED.file_version,
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
        finish_run(connection, run_id, len(records), inserted, updated)

        print("JIRA INGESTION SUCCESSFUL")
        print(f"File: {file_path} (version {file_version})")
        print(f"Processed: {len(records)}")
        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")
        print(f"Total records in Bronze: {total_rows}")

    except Exception as error:
        if run_id is not None:
            fail_run(connection, run_id, error)
        else:
            connection.rollback()
        raise

    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(
        description="Load the Jira issue sample into bronze."
    )
    parser.add_argument("--file-path", default=DEFAULT_FILE)
    parser.add_argument("--file-version", default="v1")
    parser.add_argument(
        "--run-date", default=date.today().isoformat(),
        help="Logical run date, YYYY-MM-DD."
    )
    args = parser.parse_args()

    datetime.strptime(args.run_date, "%Y-%m-%d")

    load_jira_data(args.file_path, args.file_version, args.run_date)


if __name__ == "__main__":
    main()
