
FROM apache/airflow:2.10.5-python3.11

USER root

RUN python -m venv /opt/dbt-venv \
    && /opt/dbt-venv/bin/pip install --no-cache-dir \
       dbt-postgres==1.9.0 \
       pandas==2.2.3 \
       psycopg2-binary==2.9.10

USER airflow

ENV PATH="/opt/dbt-venv/bin:${PATH}"

# FROM apache/airflow:2.10.5-python3.11

# USER root

# RUN python -m venv /opt/dbt-venv \
#     && /opt/dbt-venv/bin/pip install --no-cache-dir \
#        dbt-postgres==1.9.0 \
#        pandas==2.2.3

# USER airflow

# ENV PATH="/opt/dbt-venv/bin:${PATH}"
