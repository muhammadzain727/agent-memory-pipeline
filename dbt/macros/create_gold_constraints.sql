
{% macro create_gold_constraints() %}

{% if execute %}

{% set statements = [
    "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_date' AND conrelid = 'gold.dim_date'::regclass) THEN ALTER TABLE gold.dim_date ADD CONSTRAINT pk_dim_date PRIMARY KEY (date_key); END IF; END $$",

    "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_project' AND conrelid = 'gold.dim_project'::regclass) THEN ALTER TABLE gold.dim_project ADD CONSTRAINT pk_dim_project PRIMARY KEY (project_key); END IF; END $$",

    "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_memory_strategy' AND conrelid = 'gold.dim_memory_strategy'::regclass) THEN ALTER TABLE gold.dim_memory_strategy ADD CONSTRAINT pk_dim_memory_strategy PRIMARY KEY (memory_strategy_key); END IF; END $$",

    "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_date' AND conrelid = 'gold.fact_agent_interaction'::regclass) THEN ALTER TABLE gold.fact_agent_interaction ADD CONSTRAINT fk_fact_date FOREIGN KEY (date_key) REFERENCES gold.dim_date(date_key); END IF; END $$",

    "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_project' AND conrelid = 'gold.fact_agent_interaction'::regclass) THEN ALTER TABLE gold.fact_agent_interaction ADD CONSTRAINT fk_fact_project FOREIGN KEY (project_key) REFERENCES gold.dim_project(project_key); END IF; END $$",

    "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_memory_strategy' AND conrelid = 'gold.fact_agent_interaction'::regclass) THEN ALTER TABLE gold.fact_agent_interaction ADD CONSTRAINT fk_fact_memory_strategy FOREIGN KEY (memory_strategy_key) REFERENCES gold.dim_memory_strategy(memory_strategy_key); END IF; END $$"
] %}

{% for statement in statements %}
    {% do run_query(statement) %}
{% endfor %}

{% endif %}

{% endmacro %}
