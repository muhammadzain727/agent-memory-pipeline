
import argparse
import csv
import json
import os
from pathlib import Path
from datetime import datetime

import psycopg2


PROJECT_IDS = {100, 200, 300}


def generate_data(run_date, file_version, file_path):
    """Generate temporary Agent interaction records."""

    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    records = []

    for i in range(1, 11):
        records.append({
            "interaction_id": f"test_{run_date}_{i}",
            "user_id": (i % 5) + 1,
            "project_id": [100, 200, 300][i % 3],
            "input_tokens": 500 + (i * 100),
            "retrieval_latency_ms": 100 + (i * 15),
            "file_version": file_version
        })

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} temporary records.")
    print(f"File: {file_path}")


def validate_data(file_path):
    """Validate required fields, nulls, duplicates and numeric values."""

    with open(file_path, newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))

    required = [
        "interaction_id",
        "user_id",
        "project_id",
        "input_tokens",
        "retrieval_latency_ms",
        "file_version"
    ]

    if not records:
        raise ValueError("Dataset is empty.")

    for record in records:
        for column in required:
            if not record.get(column):
                raise ValueError(f"Null or missing value: {column}")

    ids = [record["interaction_id"] for record in records]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate interaction IDs detected.")

    for record in records:
        if int(record["input_tokens"]) < 0:
            raise ValueError("Negative input token value.")

        if float(record["retrieval_latency_ms"]) < 0:
            raise ValueError("Negative retrieval latency.")

        if int(record["project_id"]) not in PROJECT_IDS:
            raise ValueError("Invalid project relationship.")

    print("DATA QUALITY VALIDATION PASSED")
    print(f"Validated records: {len(records)}")


def load_data(file_path, run_date):
    """Load records into Bronze using idempotent upserts."""

    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "agent_memory"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

    run_id = None

    try:
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
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                INSERT INTO audit.pipeline_runs (
                    dag_id,
                    source_name,
                    status
                )
                VALUES (%s, %s, %s)
                RETURNING run_id;
            """, (
                "agent_memory_pipeline",
                "synthetic_agent_test_data",
                "RUNNING"
            ))

            run_id = cursor.fetchone()[0]
            connection.commit()

            with open(file_path, newline="", encoding="utf-8") as file:
                records = list(csv.DictReader(file))

            existing_ids = {
                record[0]
                for record in cursor.execute(
                    "SELECT interaction_id FROM bronze.agent_interactions_raw;"
                ) or []
            } if False else set()

            interaction_ids = [
                record["interaction_id"] for record in records
            ]

            cursor.execute("""
                SELECT interaction_id
                FROM bronze.agent_interactions_raw
                WHERE interaction_id = ANY(%s);
            """, (interaction_ids,))

            existing_ids = {row[0] for row in cursor.fetchall()}

            for record in records:
                payload = json.dumps(record)

                cursor.execute("""
                    INSERT INTO bronze.agent_interactions_raw (
                        interaction_id,
                        user_id,
                        project_id,
                        input_tokens,
                        retrieval_latency_ms,
                        file_version,
                        ingestion_date,
                        raw_payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)

                    ON CONFLICT (interaction_id)
                    DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        project_id = EXCLUDED.project_id,
                        input_tokens = EXCLUDED.input_tokens,
                        retrieval_latency_ms = EXCLUDED.retrieval_latency_ms,
                        file_version = EXCLUDED.file_version,
                        ingestion_date = EXCLUDED.ingestion_date,
                        raw_payload = EXCLUDED.raw_payload,
                        loaded_at = CURRENT_TIMESTAMP;
                """, (
                    record["interaction_id"],
                    int(record["user_id"]),
                    int(record["project_id"]),
                    int(record["input_tokens"]),
                    float(record["retrieval_latency_ms"]),
                    record["file_version"],
                    run_date,
                    payload
                ))

            inserted = len(set(interaction_ids) - existing_ids)
            updated = len(existing_ids)

            cursor.execute("""
                UPDATE audit.pipeline_runs
                SET status = 'SUCCESS',
                    records_processed = %s,
                    records_inserted = %s,
                    records_updated = %s
                WHERE run_id = %s;
            """, (
                len(records),
                inserted,
                updated,
                run_id
            ))

            connection.commit()

            print("BRONZE DATA LOAD SUCCESSFUL")
            print(f"Processed: {len(records)}")
            print(f"Inserted: {inserted}")
            print(f"Updated: {updated}")

    except Exception as error:
        connection.rollback()

        if run_id is not None:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE audit.pipeline_runs
                        SET status = 'FAILED',
                            error_message = %s
                        WHERE run_id = %s;
                    """, (str(error), run_id))

                connection.commit()
            except Exception:
                connection.rollback()

        raise

    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=["generate", "validate", "load"]
    )

    parser.add_argument("--run-date", required=True)
    parser.add_argument("--file-version", default="v1")
    parser.add_argument("--file-path", required=True)

    args = parser.parse_args()

    datetime.strptime(args.run_date, "%Y-%m-%d")

    if args.action == "generate":
        generate_data(
            args.run_date,
            args.file_version,
            args.file_path
        )

    elif args.action == "validate":
        validate_data(args.file_path)

    elif args.action == "load":
        load_data(args.file_path, args.run_date)


if __name__ == "__main__":
    main()
