-- Input tokens include the question and prompt overhead, so they can never be
-- smaller than the selected context.
SELECT
    interaction_id,
    input_tokens,
    selected_context_tokens
FROM {{ ref('silver_agent_interactions') }}
WHERE input_tokens < selected_context_tokens
