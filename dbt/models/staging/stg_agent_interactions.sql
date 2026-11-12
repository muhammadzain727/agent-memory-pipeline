SELECT
    interaction_id,
    interaction_timestamp AS interaction_time,
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

    loaded_at AS ingested_at

FROM bronze.agent_interactions_raw

WHERE interaction_id IS NOT NULL
  AND memory_strategy IS NOT NULL