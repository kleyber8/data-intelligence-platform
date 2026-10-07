# ============================================================
# Airflow personalizado para Data Intelligence Platform
# ============================================================
FROM apache/airflow:2.10.2-python3.11

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      git \
      curl \
 && rm -rf /var/lib/apt/lists/*
USER airflow

# Verificación de seguridad: falla el build si `airflow` no
# responde. Así nunca dejamos una imagen rota en el registro.
RUN airflow version
