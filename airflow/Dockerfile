FROM apache/airflow:2.10.2-python3.11

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      git \
      curl \
 && rm -rf /var/lib/apt/lists/*

# dbt en venv aislado para evitar conflictos con SQLAlchemy 1.4 de Airflow.
RUN python3 -m venv /opt/dbt-venv \
 && /opt/dbt-venv/bin/pip install --upgrade pip setuptools wheel \
 && /opt/dbt-venv/bin/pip install dbt-postgres

USER airflow

COPY airflow/requirements.txt /tmp/airflow-requirements.txt

# Timeout aumentado y reintentos por conexión lenta.
RUN pip install --no-cache-dir \
      --timeout 300 \
      --retries 10 \
      -r /tmp/airflow-requirements.txt \
 && airflow version

ENV DBT_PROFILES_DIR=/home/airflow/.dbt
ENV PATH="/opt/dbt-venv/bin:${PATH}"
