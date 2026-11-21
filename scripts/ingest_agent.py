"""Validate and load the synthetic Agent interactions into the bronze layer.

Usage:
    python ingest_agent.py validate --file-path <file.json>
    python ingest_agent.py load --file-path <file.json> \
        --file-version v1 --run-date 2026-11-16

The load is idempotent: rows are upserted on interaction_id, so running it
again with the same file never creates duplicates.
"""

import argparse
import json
from datetime import date, datetime

from psycopg2.extras import Json, execute_values

from db_connection import get_connection
from pipeline_audit import (
    ensure_audit_objects, fail_run, finish_run, start_run
)


DEFAULT_FILE = "/opt/airflow/data/agent/agent_conversations_v1.json"

SOURCE_NAME = "synthetic_agent_interactions"

STRATEGIES = {
    "complete_history",
    "recent_context_retrieval",
    "retrieval_compression"
}

REQUIRED_FIELDS = [
    "interaction_id",
    "timestamp",
    "user_id",
    "project_id",
    "memory_strategy",
    "input_tokens",
    "retrieval_latency_ms",
    "issue_id",
    "user_question",
    "agent_response",
    "full_history_tokens",
    "selected_context_tokens",
    "retrieved_memory_count",
    "response_latency_ms"
]

NON_NEGATIVE_FIELDS = [
    "input_tokens",
    "retrieval_latency_ms",
    "full_history_tokens",
    "selected_context_tokens",
    "retrieved_memory_count",
    "response_latency_ms"
]


def read_and_validate(file_path):
    """Read the JSON file and check every record. Returns the records.

    Raises ValueError listing the problems when any check fails.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list) or not records:
        raise ValueError("Agent dataset is empty or not a list")

    errors = []
    seen_ids = set()

    for record in records:
        record_id = record.get("interaction_id")

        missing = [
            field for field in REQUIRED_FIELDS
            if record.get(field) is None
        ]

        if missing:
            errors.append(f"{record_id}: missing {', '.join(missing)}")
            continue

        if record_id in seen_ids:
            errors.append(f"{record_id}: duplicate interaction_id")
        seen_ids.add(record_id)

        if record["memory_strategy"] not in STRATEGIES:
            errors.append(
                f"{record_id}: unknown strategy {record['memory_strategy']}"
            )

        not_numeric = [
            field for field in NON_NEGATIVE_FIELDS
            if not isinstance(record[field], (int, float))
            or isinstance(record[field], bool)
        ]

        if not_numeric:
            errors.append(
                f"{record_id}: not numeric {', '.join(not_numeric)}"
            )
            continue

        for field in NON_NEGATIVE_FIELDS:
            if record[field] < 0:
                errors.append(f"{record_id}: negative {field}")

        if record["selected_context_tokens"] > record["full_history_tokens"]:
            errors.append(
                f"{record_id}: selected context larger than full history"
            )

        if record["input_tokens"] < record["selected_context_tokens"]:
            errors.append(
                f"{record_id}: input tokens smaller than selected context"
            )

        try:
            datetime.fromisoformat(record["timestamp"])
        except (TypeError, ValueError):
            errors.append(f"{record_id}: invalid timestamp")

    if errors:
        shown = "; ".join(errors[:10])
        raise ValueError(
            f"{len(errors)} validation errors. First errors: {shown}"
        )

    return records


def validate(file_path):
    records = read_and_validate(file_path)

    print("DATA QUALITY VALIDATION PASSED")
    print(f"File: {file_path}")
    print(f"Validated records: {len(records)}")
    print(f"Unique interaction IDs: {len(records)}")


def load(file_path, file_version, run_date):
    records = read_and_validate(file_path)

    rows = [
        (
            record["interaction_id"],
            record["user_id"],
            record["project_id"],
            record["input_tokens"],
            record["retrieval_latency_ms"],
            file_version,
            run_date,
            record["timestamp"],
            record["issue_id"],
            record["user_question"],
            record["agent_response"],
            record["memory_strategy"],
            record["full_history_tokens"],
            record["selected_context_tokens"],
            record["retrieved_memory_count"],
            record["response_latency_ms"],
            Json(record)
        )
        for record in records
    ]

    connection = get_connection()
    run_id = None

    try:
        ensure_audit_objects(connection)
        run_id = start_run(connection, SOURCE_NAME, run_date)

        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bronze.agent_interactions_raw (
                    interaction_id VARCHAR(100) PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    project_id INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    retrieval_latency_ms NUMERIC(12,2) NOT NULL,
                    file_version VARCHAR(50),
                    ingestion_date DATE NOT NULL,
                    raw_payload JSONB NOT NULL,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    interaction_timestamp TIMESTAMPTZ,
                    issue_id INTEGER,
                    user_question TEXT,
                    agent_response TEXT,
                    memory_strategy TEXT,
                    full_history_tokens INTEGER,
                    selected_context_tokens INTEGER,
                    retrieved_memory_count INTEGER,
                    response_latency_ms INTEGER
                );
            """)

            # Count how many of these IDs are already in bronze, so the
            # audit row can report inserted and updated separately.
            cursor.execute("""
                SELECT COUNT(*)
                FROM bronze.agent_interactions_raw
                WHERE interaction_id = ANY(%s);
            """, ([row[0] for row in rows],))
            updated = cursor.fetchone()[0]
            inserted = len(rows) - updated

            execute_values(
                cursor,
                """
                INSERT INTO bronze.agent_interactions_raw (
                    interaction_id,
                    user_id,
                    project_id,
                    input_tokens,
                    retrieval_latency_ms,
                    file_version,
                    ingestion_date,
                    interaction_timestamp,
                    issue_id,
                    user_question,
                    agent_response,
                    memory_strategy,
                    full_history_tokens,
                    selected_context_tokens,
                    retrieved_memory_count,
                    response_latency_ms,
                    raw_payload
                )
                VALUES %s

                ON CONFLICT (interaction_id)
                DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    project_id = EXCLUDED.project_id,
                    input_tokens = EXCLUDED.input_tokens,
                    retrieval_latency_ms = EXCLUDED.retrieval_latency_ms,
                    file_version = EXCLUDED.file_version,
                    ingestion_date = EXCLUDED.ingestion_date,
                    interaction_timestamp = EXCLUDED.interaction_timestamp,
                    issue_id = EXCLUDED.issue_id,
                    user_question = EXCLUDED.user_question,
                    agent_response = EXCLUDED.agent_response,
                    memory_strategy = EXCLUDED.memory_strategy,
                    full_history_tokens = EXCLUDED.full_history_tokens,
                    selected_context_tokens = EXCLUDED.selected_context_tokens,
                    retrieved_memory_count = EXCLUDED.retrieved_memory_count,
                    response_latency_ms = EXCLUDED.response_latency_ms,
                    raw_payload = EXCLUDED.raw_payload,
                    loaded_at = CURRENT_TIMESTAMP;
                """,
                rows,
                page_size=500
            )

            cursor.execute("""
                SELECT COUNT(*) FROM bronze.agent_interactions_raw;
            """)
            total = cursor.fetchone()[0]

        connection.commit()
        finish_run(connection, run_id, len(rows), inserted, updated)

        print("AGENT INGESTION SUCCESSFUL")
        print(f"File: {file_path} (version {file_version})")
        print(f"Processed: {len(rows)}")
        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")
        print(f"Total records in Bronze: {total}")

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
        description="Validate or load the synthetic Agent interactions."
    )
    parser.add_argument("action", choices=["validate", "load"])
    parser.add_argument("--file-path", default=DEFAULT_FILE)
    parser.add_argument("--file-version", default="v1")
    parser.add_argument(
        "--run-date", default=date.today().isoformat(),
        help="Logical run date, YYYY-MM-DD."
    )
    args = parser.parse_args()

    datetime.strptime(args.run_date, "%Y-%m-%d")

    if args.action == "validate":
        validate(args.file_path)
    else:
        load(args.file_path, args.file_version, args.run_date)


if __name__ == "__main__":
    main()
