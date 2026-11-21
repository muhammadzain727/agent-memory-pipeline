import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_OUTPUT_FILE = Path(
    "/opt/airflow/data/agent/agent_conversations_v1.json"
)

DEFAULT_SEED = 42

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


def generate_records(seed=DEFAULT_SEED):
    # A local generator with a fixed seed: the same seed always gives the
    # same file, so the pipeline can be re-run and gives identical data.
    rng = random.Random(seed)

    records = []

    start_time = datetime(
        2026, 1, 1, tzinfo=timezone.utc
    )

    for i in range(1, TOTAL_RECORDS + 1):

        strategy = STRATEGIES[(i - 1) % 3]

        full_history_tokens = rng.randint(2000, 12000)

        if strategy == "complete_history":
            selected_context_tokens = full_history_tokens
            retrieved_memory_count = 0
            retrieval_latency_ms = 0

        elif strategy == "recent_context_retrieval":
            # The selected context can never be larger than the full history
            selected_context_tokens = min(
                rng.randint(1000, 3500),
                full_history_tokens
            )
            retrieved_memory_count = rng.randint(2, 8)
            retrieval_latency_ms = rng.randint(20, 100)

        else:
            selected_context_tokens = rng.randint(300, 1500)
            retrieved_memory_count = rng.randint(2, 10)
            retrieval_latency_ms = rng.randint(40, 180)

        input_tokens = (
            selected_context_tokens
            + rng.randint(100, 500)
        )

        records.append({
            "interaction_id": f"AGENT-{i:05d}",
            "timestamp": (
                start_time + timedelta(minutes=i * 15)
            ).isoformat(),
            "user_id": rng.randint(1, 100),
            "project_id": rng.choice([100, 200, 300]),
            "issue_id": rng.randint(100000, 110000),
            "user_question": rng.choice(QUESTIONS),
            "agent_response": rng.choice(RESPONSES),
            "memory_strategy": strategy,
            "full_history_tokens": full_history_tokens,
            "selected_context_tokens": selected_context_tokens,
            "input_tokens": input_tokens,
            "retrieved_memory_count": retrieved_memory_count,
            "retrieval_latency_ms": retrieval_latency_ms,
            "response_latency_ms": rng.randint(200, 2000)
        })

    return records


def main():
    parser = argparse.ArgumentParser(
        description="Generate the synthetic Agent interaction file."
    )
    parser.add_argument(
        "--output", default=str(DEFAULT_OUTPUT_FILE),
        help="Path of the JSON file to write."
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help="Random seed (default 42)."
    )
    args = parser.parse_args()

    output_file = Path(args.output)
    records = generate_records(args.seed)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)

    print("SYNTHETIC DATA GENERATION SUCCESSFUL")
    print(f"Records generated: {len(records)}")
    print(f"Seed: {args.seed}")
    print(f"Output file: {output_file}")

    for strategy in STRATEGIES:
        count = sum(
            1 for record in records
            if record["memory_strategy"] == strategy
        )
        print(f"{strategy}: {count}")


if __name__ == "__main__":
    main()
