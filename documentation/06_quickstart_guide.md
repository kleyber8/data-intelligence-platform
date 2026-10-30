# 🚀 Guía de Inicio Rápido (Quickstart en Fedora Linux)

Esta guía detalla los comandos exactos para clonar, desplegar y ejecutar la plataforma de datos de extremo a extremo en un entorno local Fedora Linux (utilizando Docker, Python y dbt).

## Pre-requisitos del Sistema
*   **Fedora Linux** (probado en 44).
*   **Docker Engine** ≥ 24 y **Docker Compose v2**.
*   **Python** ≥ 3.11 (probado en 3.14).
*   **dbt-postgres** instalado en `~/.venvs/dbt` y expuesto en `~/.local/bin/dbt`.

## Paso 1: Clonar y Preparar el Entorno

```bash
# 1. Clonar el repositorio
git clone git@github.com:kleyber8/data-intelligence-platform.git
cd data-intelligence-platform

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Generar la FERNET_KEY para Airflow y añadirla al .env
echo "AIRFLOW__CORE__FERNET_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env

# 4. Añadir el UID del usuario para permisos de archivos
echo "AIRFLOW_UID=$(id -u)" >> .env
```

## Paso 2: Crear el Entorno Virtual e Instalar Dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt
```

## Paso 3: Levantar la Infraestructura (Docker)

Este comando descarga las imágenes (Airflow, PostgreSQL, MinIO) y compila la imagen personalizada de Airflow con dbt integrado. *(Nota: La primera vez puede tardar de 5 a 15 minutos)*.

```bash
cd docker
docker compose --env-file ../.env up -d --build
cd ..
```

**Verificar que todo esté saludable:**
```bash
docker compose --env-file .env ps
# Debes ver 5 contenedores en estado "healthy" o "running"
```

## Paso 4: Aplicar Seguridad (RBAC)

Antes de ejecutar datos, aplicamos el principio de mínimo privilegio en PostgreSQL:

```bash
./scripts/security/apply_rbac.sh
```
*(Esto crea los 4 usuarios: `pipeline_user`, `dbt_user`, `api_user` y `analyst_user`)*.

## Paso 5: Ejecutar el Pipeline de Datos (Fases 2, 3 y 4)

```bash
source .venv/bin/activate
set -a; source .env; set +a

# 1. Ingestión (Genera datos sintéticos y los guarda en MinIO)
python -m ingestion.maritime.noaa_ais --source synthetic

# 2. Carga a Bronze y Quality Gate 1
export RUN_ID=$(docker exec dip-project-postgres psql -U maritime_user -d maritime -t -A -c "SELECT ingestion_run_id FROM metadata.ingestion_runs ORDER BY created_at DESC LIMIT 1")
python -c "from src.storage.bronze_writer import write_bronze_from_landing; write_bronze_from_landing('$RUN_ID')"
python -c "from src.validation.quality_gate_1 import run_quality_gate_1; run_quality_gate_1('$RUN_ID')"

# 3. Transformaciones dbt (Silver y Gold)
cd dbt/maritime
export DBT_PROFILES_DIR=~/.dbt
dbt deps
dbt run --select tag:silver --no-version-check
dbt run --select tag:gold --no-version-check
dbt test --select tag:silver --no-version-check
dbt test --select tag:gold --no-version-check
cd ../..
```

## Paso 6: Levantar la API REST (Fase 6)

En una nueva pestaña de la terminal:

```bash
cd ~/Projects/data-intelligence-platform
source .venv/bin/activate
uvicorn api.app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 🖥️ Panel de Control Local (Interfaces Visuales)

Con la plataforma en ejecución, puedes auditar y visualizar el estado del ecosistema en las siguientes interfaces (haz clic para abrirlas):

| Interfaz | URL Local | Credenciales | Propósito |
| :--- | :--- | :--- | :--- |
| 🌪️ **Apache Airflow** | [http://localhost:8080](http://localhost:8080) | `admin` / `admin` | Orquestación de DAGs y logs de ejecución. |
| ⚡ **FastAPI Swagger** | [http://localhost:8001/docs](http://localhost:8001/docs) | *(JWT Auth)* | Explorador interactivo de los endpoints de la API. |
| 🗄️ **MinIO Console** | [http://localhost:9001](http://localhost:9001) | `minioadmin` / `minioadmin` | Navegador del Data Lake (archivos Parquet). |
| 🐘 **pgAdmin** | [http://localhost:5050](http://localhost:5050) | `admin@example.com` / `admin` | Administración gráfica de PostgreSQL. |
| 🐳 **Portainer** | [https://localhost:9443](https://localhost:9443) | *(Crear en 1er inicio)* | Monitor de contenedores (CPU/RAM). |
| 📊 **dbt Docs** | Ejecutar `./scripts/serve_dbt_docs.sh` | *(Automático)* | Catálogo visual y grafo de linaje. |

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
