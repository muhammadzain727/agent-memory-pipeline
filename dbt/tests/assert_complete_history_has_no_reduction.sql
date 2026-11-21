-- The complete_history strategy passes the whole history, so its context
-- reduction must be exactly 0.
SELECT
    interaction_id,
    context_reduction_pct
FROM {{ ref('fact_agent_interaction') }}
WHERE memory_strategy_key = 'complete_history'
  AND context_reduction_pct <> 0
