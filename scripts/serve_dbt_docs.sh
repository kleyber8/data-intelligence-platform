#!/usr/bin/env bash
# Levanta la interfaz visual de dbt en el puerto 8081
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/dbt/maritime"

set -a; source "$PROJECT_ROOT/.env"; set +a
export DBT_PROFILES_DIR=~/.dbt

echo "→ Generando documentación de dbt..."
dbt docs generate --no-version-check

echo ""
echo "→ Sirviendo UI en http://localhost:8081 (Ctrl+C para detener)"
dbt docs serve --port 8081 --no-browser
