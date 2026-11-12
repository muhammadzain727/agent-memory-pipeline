
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

OUTPUT_FILE = Path(
    "/opt/airflow/data/agent/agent_conversations.json"
)

TOTAL_RECORDS = 5000

STRATEGIES = [
    "complete_history",
    "recent_context_retrieval",
    "retrieval_compression"
]

QUESTIONS = [
    "What was the last decision made about this issue?",
    "Can you summarize the previous project discussion?",
    "What changes were made to this issue?",
    "What should be the next action for this project?",
    "Can you retrieve the relevant historical information?"
]

RESPONSES = [
    "Based on the available project history, here is the relevant information.",
    "The previous discussions indicate the following decision and next steps.",
    "The historical issue records provide the context needed for this answer.",
    "Here is a summary of the relevant project information."
]


def generate_records():
    records = []

    start_time = datetime(
        2026, 1, 1, tzinfo=timezone.utc
    )

    for i in range(1, TOTAL_RECORDS + 1):

        strategy = STRATEGIES[(i - 1) % 3]

        full_history_tokens = random.randint(2000, 12000)

        if strategy == "complete_history":
            selected_context_tokens = full_history_tokens
            retrieved_memory_count = 0
            retrieval_latency_ms = 0

        elif strategy == "recent_context_retrieval":
            selected_context_tokens = random.randint(
                1000, 3500
            )
            retrieved_memory_count = random.randint(2, 8)
            retrieval_latency_ms = random.randint(20, 100)

        else:
            selected_context_tokens = random.randint(
                300, 1500
            )
            retrieved_memory_count = random.randint(2, 10)
            retrieval_latency_ms = random.randint(40, 180)

        input_tokens = (
            selected_context_tokens
            + random.randint(100, 500)
        )

        records.append({
            "interaction_id": f"AGENT-{i:05d}",
            "timestamp": (
                start_time + timedelta(minutes=i * 15)
            ).isoformat(),
            "user_id": random.randint(1, 100),
            "project_id": random.choice([100, 200, 300]),
            "issue_id": random.randint(100000, 110000),
            "user_question": random.choice(QUESTIONS),
            "agent_response": random.choice(RESPONSES),
            "memory_strategy": strategy,
            "full_history_tokens": full_history_tokens,
            "selected_context_tokens": selected_context_tokens,
            "input_tokens": input_tokens,
            "retrieved_memory_count": retrieved_memory_count,
            "retrieval_latency_ms": retrieval_latency_ms,
            "response_latency_ms": random.randint(200, 2000)
        })

    return records


def main():
    records = generate_records()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(records, file, indent=2)

    print("SYNTHETIC DATA GENERATION SUCCESSFUL")
    print(f"Records generated: {len(records)}")
    print(f"Output file: {OUTPUT_FILE}")

    for strategy in STRATEGIES:
        count = sum(
            1 for record in records
            if record["memory_strategy"] == strategy
        )
        print(f"{strategy}: {count}")


if __name__ == "__main__":
    main()
