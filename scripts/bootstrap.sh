#!/usr/bin/env bash
# scripts/bootstrap.sh
# Crea la estructura de directorios del proyecto.
set -euo pipefail

PROJECT_ROOT="${HOME}/Projects/data-intelligence-platform"
mkdir -p "${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

DIRS=(
  "architecture/diagrams"
  "data/raw" "data/bronze" "data/silver" "data/gold"
  "data/quarantine" "data/metadata"
  "ingestion/maritime" "ingestion/ports" "ingestion/weather"
  "src/storage" "src/ingestion" "src/validation" "src/geospatial"
  "src/tracking" "src/features" "src/ml"
  "airflow/dags" "airflow/plugins" "airflow/logs" "airflow/config"
  "dbt/maritime/models/staging"
  "dbt/maritime/models/intermediate"
  "dbt/maritime/models/marts/core"
  "dbt/maritime/models/marts/port_operations"
  "dbt/maritime/models/marts/port_congestion"
  "dbt/maritime/models/marts/vessel_intelligence"
  "dbt/maritime/models/marts/route_intelligence"
  "dbt/maritime/models/marts/anomaly"
  "dbt/maritime/snapshots" "dbt/maritime/tests" "dbt/maritime/macros"
  "dbt/maritime/seeds" "dbt/maritime/analyses"
  "api/app/routers" "api/app/schemas" "api/tests"
  "ml/training" "ml/evaluation" "ml/models"
  "intelligence/prompts" "intelligence/schemas" "intelligence/gemini"
  "postman"
  "docker/postgres/init" "docker/minio"
  "scripts"
  "tests/unit" "tests/integration" "tests/data_quality"
  "dashboards" "monitoring"
  "docs/decisions" "docs/incidents" "docs/experiments" "docs/cost-optimization"
)

for d in "${DIRS[@]}"; do
  mkdir -p "${d}"
done

# Archivos .gitkeep para preservar carpetas vacías en Git
find . -type d -empty -exec touch {}/.gitkeep \;

echo "Estructura creada en ${PROJECT_ROOT}"
tree -L 3 -a -I '.git|.venv|__pycache__|*.pyc' "${PROJECT_ROOT}" || true
