SELECT
    interaction_id,
    interaction_time,
    user_id,
    project_id,
    issue_id,
    user_question,
    agent_response,
    memory_strategy,

    full_history_tokens,
    selected_context_tokens,
    input_tokens,

    retrieved_memory_count,
    retrieval_latency_ms,
    response_latency_ms,

    ingested_at

FROM {{ ref('stg_agent_interactions') }}

WHERE input_tokens >= 0
  AND full_history_tokens >= 0
  AND selected_context_tokens >= 0
  AND retrieved_memory_count >= 0
  AND retrieval_latency_ms >= 0
  AND response_latency_ms >= 0