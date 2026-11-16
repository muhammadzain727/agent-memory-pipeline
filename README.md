# Data Engineering for Long Term AI Agent Memory Management

## 1. Project Overview

This project develops a data engineering pipeline to study how different memory management strategies can reduce the amount of historical context required by AI Agents.

The project combines public Jira issue data with synthetic AI Agent interaction data. It uses Apache Airflow for pipeline orchestration, PostgreSQL for data storage, and dbt for data transformations and quality testing.

The main objective is to organize historical data and evaluate three memory strategies:

1. Complete History
2. Recent Context with Retrieval
3. Retrieval with Compression

**Important:** AI Agent interactions and their token and latency measurements are synthetic experimental data. They do not represent real production Agent performance.

## 2. Technologies Used

* Python for data generation and ingestion
* PostgreSQL 16 for database storage
* Apache Airflow for pipeline orchestration
* dbt for data transformations and testing
* Docker Compose for environment management
* SQL for analytical queries

## 3. Data Sources

The project uses two data sources:

**Jira Dataset**

Public Jira issue data containing historical project and issue information. The pipeline processes a sample of 10,000 Jira issues.

**Synthetic Agent Interaction Dataset**

Approximately 5,000 synthetic Agent interactions containing timestamps, project information, memory strategies, token counts, retrieved memory counts and latency measurements.

## 4. Data Architecture

The project follows the Medallion Architecture.

* **Bronze:** Stores raw Jira and Agent interaction records.
* **Staging:** Provides initial views and extracts required fields from raw data.
* **Silver:** Stores cleaned and structured datasets.
* **Gold:** Contains analytical dimensions and fact tables.

The Gold layer uses a star schema with one fact table and three dimension tables.

**Fact table:** `fact_agent_interaction`

**Dimension tables:**
* `dim_date`
* `dim_project`
* `dim_memory_strategy`

Primary and foreign key constraints maintain relationships between the fact table and dimensions.

## 5. Airflow Pipeline

Airflow orchestrates the complete pipeline through seven tasks:

1. Generate synthetic Agent data.
2. Validate generated data.
3. Load Agent data into Bronze.
4. Load Jira data into Bronze.
5. Execute dbt transformations.
6. Create Gold primary and foreign key relationships.
7. Execute dbt data quality tests.

The pipeline supports date and file version parameters. Jira ingestion uses upsert logic to avoid duplicate issue records.

## 6. dbt Transformations

The project contains eight dbt models:

* Two staging views
* Two Silver tables
* Three Gold dimension tables
* One Gold fact table

The Gold relationships are created through a dbt macro executed by Airflow after the transformations.

The project includes 11 dbt data quality tests covering uniqueness and non null requirements.

## 7. Analytical Questions

The Gold layer supports five analytical questions:

1. How much context can be reduced using different memory strategies?
2. How does input token consumption differ between strategies?
3. How does memory retrieval latency differ?
4. Which projects generate the highest number of Agent interactions?
5. How many historical memories are typically retrieved per interaction?

## 8. Experimental Results

The synthetic experiment produced the following results:

| Memory strategy | Context reduction | Average input tokens | Retrieval latency |
|---|---:|---:|---:|
| Retrieval with Compression | 83.80% | 1,206.49 | 108.54 ms |
| Recent Context with Retrieval | 58.90% | 2,597.08 | 60.35 ms |
| Complete History | 0.00% | 7,289.87 | 0.00 ms |

These results demonstrate the tradeoff between context reduction, token consumption and retrieval latency within the synthetic experiment.

## 9. Running the Project

### Prerequisites

* Docker Desktop
* Git
* PostgreSQL compatible database client, such as pgAdmin

### Setup

Clone the repository:

```bash
git clone https://github.com/muhammadzain727/agent-memory-pipeline.git
cd agent-memory-pipeline
```

Create the environment file:

```bash
cp .env.example .env
```

Configure the required environment variables in `.env`.

Ensure the Jira dataset and extracted JSONL file are available at the paths expected by the ingestion script. Large source datasets are not included in the Git repository.

Build and start the containers:

```bash
docker compose build
docker compose up -d
```

Open Airflow:

```text
http://localhost:8080
```

Trigger the `agent_memory_pipeline` DAG to execute the complete workflow.

### Run dbt manually

```bash
docker compose exec airflow /opt/dbt-venv/bin/dbt run --project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt
```

Run data quality tests:

```bash
docker compose exec airflow /opt/dbt-venv/bin/dbt test --project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt
```

## 10. Team Contributions

| Team member | Contribution |
|---|---:|
| Muhammad Zain | 40% |
| Hashim Ali | 40% |
| Karl Ingmar Adamson | 20% |

## 11. AI Assistance Disclosure

AI tools were used to support development, troubleshooting, SQL writing, documentation and understanding of data engineering concepts. The team reviewed and tested the implemented pipeline.

## 12. Project Limitations

The Agent interaction dataset is synthetic. Token consumption, retrieval latency and memory retrieval results are generated experimental values. They should not be interpreted as measurements from a real production AI Agent system.