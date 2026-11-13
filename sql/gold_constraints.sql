
-- Create primary keys on Gold dimensions
ALTER TABLE gold.dim_date
ADD CONSTRAINT pk_dim_date PRIMARY KEY (date_key);

ALTER TABLE gold.dim_project
ADD CONSTRAINT pk_dim_project PRIMARY KEY (project_key);

ALTER TABLE gold.dim_memory_strategy
ADD CONSTRAINT pk_dim_memory_strategy
PRIMARY KEY (memory_strategy_key);

-- Create foreign keys from fact to dimensions
ALTER TABLE gold.fact_agent_interaction
ADD CONSTRAINT fk_fact_date
FOREIGN KEY (date_key)
REFERENCES gold.dim_date(date_key);

ALTER TABLE gold.fact_agent_interaction
ADD CONSTRAINT fk_fact_project
FOREIGN KEY (project_key)
REFERENCES gold.dim_project(project_key);

ALTER TABLE gold.fact_agent_interaction
ADD CONSTRAINT fk_fact_memory_strategy
FOREIGN KEY (memory_strategy_key)
REFERENCES gold.dim_memory_strategy(memory_strategy_key);
