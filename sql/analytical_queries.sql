
-- Query 1: Context reduction by memory strategy
SELECT
    memory_strategy_key,
    ROUND(AVG(context_reduction_pct), 2) AS avg_context_reduction_pct
FROM gold.fact_agent_interaction
GROUP BY memory_strategy_key
ORDER BY avg_context_reduction_pct DESC;


-- Query 2: Average input tokens by memory strategy
SELECT
    memory_strategy_key,
    ROUND(AVG(input_tokens), 2) AS avg_input_tokens
FROM gold.fact_agent_interaction
GROUP BY memory_strategy_key
ORDER BY avg_input_tokens;


-- Query 3: Average retrieval latency by memory strategy
SELECT
    memory_strategy_key,
    ROUND(AVG(retrieval_latency_ms), 2) AS avg_retrieval_latency_ms
FROM gold.fact_agent_interaction
GROUP BY memory_strategy_key
ORDER BY avg_retrieval_latency_ms;


-- Query 4: Number of interactions by project
SELECT
    project_key,
    COUNT(*) AS total_interactions
FROM gold.fact_agent_interaction
GROUP BY project_key
ORDER BY total_interactions DESC;


-- Query 5: Average number of retrieved memories
SELECT
    memory_strategy_key,
    ROUND(AVG(retrieved_memory_count), 2) AS avg_retrieved_memories
FROM gold.fact_agent_interaction
GROUP BY memory_strategy_key
ORDER BY avg_retrieved_memories DESC;
