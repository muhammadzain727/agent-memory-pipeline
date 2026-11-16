
import json
from pathlib import Path

from db_connection import get_connection
from psycopg2.extras import Json, execute_values


DATA_FILE = Path(
    "/opt/airflow/data/agent/agent_conversations.json"
)


def load_agent_data():
    # Check that the source file exists
    if not DATA_FILE.exists():
        raise FileNotFoundError(DATA_FILE)

    # Read the synthetic Agent dataset
    with DATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list) or not records:
        raise ValueError("Agent dataset is empty or invalid")

    rows = []
    seen_ids = set()

    # Validate records and prepare database rows
    for record in records:

        required = [
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

        for field in required:
            if record.get(field) is None:
                raise ValueError(
                    f"Missing {field} in "
                    f"{record.get('interaction_id')}"
                )

        interaction_id = record["interaction_id"]

        # Prevent duplicate IDs within the source file
        if interaction_id in seen_ids:
            raise ValueError(
                f"Duplicate interaction ID: {interaction_id}"
            )

        seen_ids.add(interaction_id)

        rows.append((
            interaction_id,
            record["user_id"],
            record["project_id"],
            record["input_tokens"],
            record["retrieval_latency_ms"],
            record["timestamp"][:10],
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
        ))

    print(f"Validated records: {len(rows)}")
    print(f"Unique interaction IDs: {len(seen_ids)}")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # Create the table if it does not exist
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

            # Insert or update records using interaction_id
            execute_values(
                cursor,
                """
                INSERT INTO bronze.agent_interactions_raw (
                    interaction_id,
                    user_id,
                    project_id,
                    input_tokens,
                    retrieval_latency_ms,
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
                page_size=100
            )

            # Count all records currently in Bronze
            cursor.execute("""
                SELECT COUNT(*)
                FROM bronze.agent_interactions_raw;
            """)

            total = cursor.fetchone()[0]

        connection.commit()

        print("\nAGENT INGESTION SUCCESSFUL")
        print(f"Records processed: {len(rows)}")
        print(f"Total records in Bronze: {total}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    load_agent_data()
