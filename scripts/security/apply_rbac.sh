#!/usr/bin/env bash
# apply_rbac.sh — Aplica el script RBAC usando contraseñas del .env
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Cargar .env
set -a
source "$PROJECT_ROOT/.env"
set +a

# Contraseñas para los nuevos roles
PIPELINE_PASSWORD="${PIPELINE_PASSWORD:-pipeline_dev_only}"
DBT_PASSWORD="${DBT_PASSWORD:-dbt_dev_only}"
API_PASSWORD="${API_PASSWORD:-api_dev_only}"
ANALYST_PASSWORD="${ANALYST_PASSWORD:-analyst_dev_only}"

echo "→ Aplicando RBAC en PostgreSQL..."
docker exec -i dip-project-postgres psql \
    -U maritime_user -d maritime \
    -v pipeline_pass="'${PIPELINE_PASSWORD}'" \
    -v dbt_pass="'${DBT_PASSWORD}'" \
    -v api_pass="'${API_PASSWORD}'" \
    -v analyst_pass="'${ANALYST_PASSWORD}'" \
    < scripts/security/init_rbac_roles.sql

echo ""
echo "→ Verificando usuarios creados:"
docker exec dip-project-postgres psql -U maritime_user -d maritime -c "\du"
