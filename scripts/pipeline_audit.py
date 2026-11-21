"""Audit helpers.

Every ingestion run writes one row to audit.pipeline_runs: a RUNNING row when
the run starts, then SUCCESS (with record counts) or FAILED (with the error).
"""

import os


def ensure_audit_objects(connection):
    """Create the schemas and the audit table if they are missing."""

    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS audit;")
        cursor.execute("""
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
        """)
    connection.commit()


def start_run(connection, source_name, run_date):
    """Insert a RUNNING row and return its run_id."""

    dag_id = os.getenv("AIRFLOW_CTX_DAG_ID", "manual_run")

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO audit.pipeline_runs
                (dag_id, execution_date, source_name, status)
            VALUES (%s, %s, %s, 'RUNNING')
            RETURNING run_id;
        """, (dag_id, run_date, source_name))
        run_id = cursor.fetchone()[0]

    connection.commit()
    return run_id


def finish_run(connection, run_id, processed, inserted, updated):
    """Mark a run as SUCCESS and store the record counts."""

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE audit.pipeline_runs
            SET status = 'SUCCESS',
                records_processed = %s,
                records_inserted = %s,
                records_updated = %s
            WHERE run_id = %s;
        """, (processed, inserted, updated, run_id))

    connection.commit()


def fail_run(connection, run_id, error):
    """Mark a run as FAILED and store the error message."""

    connection.rollback()

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE audit.pipeline_runs
            SET status = 'FAILED',
                error_message = %s
            WHERE run_id = %s;
        """, (str(error)[:2000], run_id))

    connection.commit()
