
import pandas as pd

from data_quality import (
    check_required_columns,
    check_null_values,
    check_duplicates,
    check_non_negative,
    check_relationships,
    print_quality_report
)


# Temporary test dataset
interactions = pd.DataFrame({
    "interaction_id": [101, 102, 103, 104],
    "user_id": [1, 2, 1, 3],
    "project_id": [10, 10, 20, 20],
    "input_tokens": [500, 700, 800, 600],
    "retrieval_latency_ms": [120, 150, 200, 180]
})
# interactions = pd.DataFrame({
#     "interaction_id": [101, 102, 102, 104],
#     "user_id": [1, 2, 1, 3],
#     "project_id": [10, 10, 99, 20],
#     "input_tokens": [500, -700, 800, 600],
#     "retrieval_latency_ms": [120, 150, 200, 180]
# })

# Temporary parent dataset
projects = pd.DataFrame({
    "project_id": [10, 20, 30],
    "project_name": ["Project A", "Project B", "Project C"]
})


results = [

    check_required_columns(
        interactions,
        [
            "interaction_id",
            "user_id",
            "project_id",
            "input_tokens"
        ]
    ),

    check_null_values(
        interactions,
        [
            "interaction_id",
            "user_id",
            "project_id"
        ]
    ),

    check_duplicates(
        interactions,
        ["interaction_id"]
    ),

    check_non_negative(
        interactions,
        [
            "input_tokens",
            "retrieval_latency_ms"
        ]
    ),

    check_relationships(
        interactions,
        "project_id",
        projects,
        "project_id"
    )
]


success = print_quality_report(results)

if not success:
    raise ValueError("Data quality validation failed.")

print("\nAll temporary data quality tests passed.")
