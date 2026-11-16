{{ config(materialized='table') }}

SELECT
    a.interaction_id,

    CAST(a.interaction_time AS DATE) AS date_key,

    a.project_id AS project_key,

    a.memory_strategy AS memory_strategy_key,

    a.user_id,
    a.issue_id,

    a.full_history_tokens,
    a.selected_context_tokens,
    a.input_tokens,

    a.retrieved_memory_count,
    a.retrieval_latency_ms,
    a.response_latency_ms,

    CASE
        WHEN a.full_history_tokens > 0
        THEN ROUND(
            (
                1.0 -
                a.selected_context_tokens::NUMERIC
                / a.full_history_tokens
            ) * 100,
            2
        )
        ELSE NULL
    END AS context_reduction_pct

FROM {{ ref('silver_agent_interactions') }} a

INNER JOIN {{ ref('dim_date') }} d
    ON CAST(a.interaction_time AS DATE) = d.date_key

INNER JOIN {{ ref('dim_project') }} p
    ON a.project_id = p.project_key

INNER JOIN {{ ref('dim_memory_strategy') }} m
    ON a.memory_strategy = m.memory_strategy_key
