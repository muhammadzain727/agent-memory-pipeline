-- Fails when any interaction passes more context to the LLM than the full history holds.
SELECT
    interaction_id,
    selected_context_tokens,
    full_history_tokens
FROM {{ ref('silver_agent_interactions') }}
WHERE selected_context_tokens > full_history_tokens
