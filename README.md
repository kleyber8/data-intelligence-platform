<div align="center">

# Data Intelligence Platform

### Una infraestructura abierta de conocimiento para el ciclo de vida completo del dato.

**De los `datos` a la `decisión`, sin cajas negras.**

[![Arquitectura](https://img.shields.io/badge/arquitectura-Medallion-1f7a8c?style=flat-square)](#-arquitectura-de-referencia)
[![Estrategia](https://img.shields.io/badge/estrategia-Local--First%20%2B%20Cloud--Ready-0f2942?style=flat-square)](#-arquitectura-de-referencia)
[![Entorno](https://img.shields.io/badge/entorno-Fedora%20Linux-1f7a8c?style=flat-square)](#-guía-de-inicio-rápido)
[![Stack](https://img.shields.io/badge/stack-Python%20%C2%B7%20Docker%20%C2%B7%20Airflow%20%C2%B7%20dbt%20%C2%B7%20PostgreSQL-0f2942?style=flat-square)](#-stack-tecnológico)
[![Estado](https://img.shields.io/badge/estado-Fase%203%20%C2%B7%20Capa%20Silver%20y%20dbt%20completados-2f855a?style=flat-square)](#-estado-de-avance)
[![Licencia](https://img.shields.io/badge/licencia-MIT-5b6b7a?style=flat-square)](#-licencia)

</div>

---

## 🌍 Propósito y Visión

Este proyecto nace de una convicción sencilla: **comprender el ciclo de vida del dato debería estar al alcance de cualquier persona**, sin depender de herramientas privadas ni de "cajas negras" que oculten la mecánica real de los sistemas modernos de datos.

No es un ejercicio académico aislado ni una solución propietaria. Es una **infraestructura abierta de conocimiento**: un repositorio que documenta, desde la primera línea de código hasta el último modelo de inteligencia, cómo se diseña, se implementa, se opera y se evoluciona una plataforma de datos completa. Cada decisión técnica está registrada con su contexto, sus alternativas y sus consecuencias, de modo que cualquier persona pueda estudiar, reproducir, cuestionar y extender este trabajo.

La plataforma se organiza alrededor de una secuencia que conecta la materia prima con la acción:

```
DATOS  →  INFORMACIÓN  →  ANÁLISIS  →  CONOCIMIENTO  →  INTELIGENCIA  →  DECISIÓN
```

Cada flecha de esa cadena corresponde a una etapa técnica concreta: ingestión, transformación, modelado analítico, detección de patrones, capacidades predictivas y generación de inteligencia accionable. El proyecto demuestra cómo cada una de esas etapas se articula con las demás para convertir un flujo crudo de observaciones en una herramienta útil para la toma de decisiones.

### Caso de estudio inicial: Tráfico Marítimo (AIS)

El primer dominio donde se materializa la arquitectura es el **tráfico marítimo**, elegido por su riqueza estructural: combina datos temporales, geoespaciales, entidades relacionadas, grandes volúmenes de observaciones y patrones complejos que se extienden en el tiempo y el espacio. Es un escenario exigente que pone a prueba toda la arquitectura.

**Sin embargo, este dominio no es el límite conceptual del proyecto.** La arquitectura está diseñada explícitamente para ser **agnóstica al dominio**, de modo que cualquier persona pueda extenderla hacia otros campos —clima, finanzas, datos urbanos, datos ambientales, datos deportivos, datos científicos, datos gubernamentales, sensores industriales— sin tener que rediseñar los componentes existentes. El caso marítimo es la primera prueba, no la frontera.

---

## 🏛️ Arquitectura de Referencia

El flujo de datos sigue el **patrón Medallion**, enriquecido con **tres Quality Gates** que garantizan la trazabilidad y calidad del dato en cada transición de capa:

```
FUENTES DE DATOS
        ↓
DISCOVERY
        ↓
INGESTIÓN
        ↓
LANDING / DATA LAKE  (MinIO local · AWS S3 cloud)
        ↓
BRONZE               (fidelidad respecto a la fuente)
        ↓
QUALITY GATE 1       (integridad estructural)
        ↓
SILVER               (normalización · reconstrucción · enriquecimiento)
        ↓
QUALITY GATE 2       (integridad referencial · continuidad)
        ↓
GOLD                 (Data Marts orientados a análisis)
        ↓
QUALITY GATE 3       (calidad analítica · ausencia de leakage)
        ↓
CONSUMO
 ┌───────────────┬──────────────┬───────────────┐
 │               │              │               │
API          DASHBOARDS       ML         INTELLIGENCE
 │               │              │               │
 └───────────────┴──────────────┴───────────────┘
        ↓
MONITORING / OBSERVABILITY
        ↓
ARCHIVE / REPROCESSING
```

**Apache Airflow** coordina las dependencias, ejecuciones, reintentos y periodicidad de todo el flujo. **dbt** gestiona las transformaciones analíticas entre capas. **PostgreSQL** materializa el modelo dimensional. **MinIO** emula S3 durante el desarrollo local, garantizando que la migración a cloud sea un cambio de endpoint, no un rediseño.

### Principios Rectores

| Principio | Significado concreto |
|---|---|
| **Reproducibilidad** | Cualquier persona puede levantar el proyecto completo con instrucciones documentadas. Nada depende de configuraciones no versionadas. |
| **Trazabilidad** | Cada registro tiene un `ingestion_run_id` que permite rastrear su origen, transformaciones y destino. |
| **Cuarentena de datos inválidos** | Los registros que fallan un Quality Gate no se eliminan en silencio: se preservan con causa y regla violada. |
| **Observabilidad** | Freshness, conteos, nulos, duplicados, schema drift e integridad referencial se monitorean activamente. |
| **Local-First + Cloud-Where-Useful** | El desarrollo y la experimentación ocurren localmente; la nube se incorpora donde aporta valor real. |
| **Desacoplamiento del dominio** | Los componentes no asumen el caso marítimo; cualquier dominio puede integrarse sin destruir lo existente. |

---

## 📊 Estado de Avance

### ✅ Fase 1 — Bootstrap completado

La fase de inicialización de la plataforma está **cerrada y verificada**. El entorno local es completamente funcional y reproducible.

| Componente | Estado | Verificación |
|---|---|---|
| **Estructura modular del repositorio** | ✅ | Estructura Medallion completa en `data/` y `dbt/` |
| **Data Lake local** | ✅ | `data/{raw,bronze,silver,gold,quarantine,metadata}` particionado tipo Hive |
| **Stack Docker orquestado** | ✅ | 5 servicios con redes y volúmenes aislados |
| **PostgreSQL analítico** | ✅ | Puerto 5432 · 5 esquemas Medallion + metadata |
| **PostgreSQL de Airflow** | ✅ | Puerto 5433 · metadata del orquestador |
| **MinIO (S3 emulator)** | ✅ | Puertos 9000 (API) y 9001 (consola) · 2 buckets creados |
| **Apache Airflow 2.10.2** | ✅ | Webserver + Scheduler `healthy` · admin creado |
| **dbt 1.12** | ✅ | `dbt debug` → *All checks passed!* |
| **Configuración tipada (Pydantic)** | ✅ | `src/config.py` con validación de tipos |
| **Entorno Python aislado** | ✅ | `.venv` con 24+ librerías verificadas |
| **Calidad de código** | ✅ | Ruff · mypy · pytest · pre-commit configurados |
| **Control de secretos** | ✅ | `.gitignore` validado · `.env.example` documentado |

### ✅ Fase 2 — Pipeline Real de Ingestión, Bronze y Quality Gate 1 completado

Primer pipeline end-to-end funcionando: extracción desde fuente sintética (o NOAA real), preservación inmutable en Data Lake y MinIO, estructuración en Bronze con auditoría completa, y validación estructural con aislamiento de registros inválidos en cuarentena.

**Métricas de la corrida de verificación:**

| Métrica | Valor |
|---|---|
| Registros procesados | 200 |
| Registros validados | 170 (85%) |
| Registros en cuarentena | 30 (15%) |
| DAG `dag_01_discovery_ingestion` | 5 tareas en TaskFlow API |

### ✅ Fase 3 — Capa Silver, Transformaciones dbt y Quality Gate 2 completado

Pipeline de transformación analítica completo: tres modelos dbt que normalizan, enriquecen y reconstruyen trayectorias; 17 tests declarativos ejecutados en verde; Quality Gate 2 validando integridad referencial, continuidad temporal y continuidad espacial; orquestación completa con DAG 02 y dbt en venv aislado dentro del contenedor.

| Componente | Estado | Evidencia verificada |
|---|---|---|
| **Modelo `stg_ais_position`** | ✅ | Normalización, casteo y filtrado por `quality_status='validated'` |
| **Modelo `int_vessel_position_deltas`** | ✅ | Haversine en SQL, deltas temporales, velocidad calculada vs reportada |
| **Modelo `int_vessel_tracks`** | ✅ | Segmentación con corte a 2h, `track_id` único por tramo continuo |
| **Macro `generate_schema_name`** | ✅ | Override del prefijado automático de dbt |
| **Tests dbt** | ✅ | `PASS=17` `ERROR=0` `WARN=0` |
| **Quality Gate 2** | ✅ | 3 reglas · 0 violaciones |
| **DAG `dag_02_silver_transformation`** | ✅ | 5 tareas · TaskFlow API + BashOperator |
| **dbt aislado en Airflow** | ✅ | Venv `/opt/dbt-venv` dentro del contenedor |

**Métricas reales de la corrida de verificación:**

| Métrica | Valor |
|---|---|
| Modelos Silver creados | 3 vistas en esquema `silver` |
| Tests dbt pasados | 17 / 17 |
| Violaciones detectadas por QG2 | 0 (referential + temporal + spatial) |
| Velocidad calculada vs reportada | Delta < 0.05 nudos |
| `is_speed_anomaly` en tracks | 0 falsos positivos |
| Distancias entre posiciones | 3.6 – 14.7 km (plausibles) |

**Aprendizajes técnicos de las tres fases:**
- Compatibilidad de Polars con CPUs sin AVX2 (`polars-lts-cpu`).
- Migración a espejo comunitario `coollabsio/minio` tras remoción de imágenes oficiales.
- Alineación del entrypoint de Airflow y fijación de providers para evitar Airflow 3.x.
- Resolución DNS del daemon Docker en Fedora (`/etc/docker/daemon.json`).
- UUID vs VARCHAR en tablas llenadas vía pandas.
- Compatibilidad SQLAlchemy 1.4 / 2.0 (`from sqlalchemy.engine import Engine`).
- Reconstrucción de las tres imágenes de Airflow al cambiar el Dockerfile.
- Macro `generate_schema_name` para evitar prefijado `silver_silver` en dbt.
- dbt en venv aislado dentro del contenedor de Airflow (`/opt/dbt-venv`).
- Conflictos de puerto entre servicios del sistema y contenedores (PostgreSQL 5432).
- Generación sintética con trayectorias físicamente coherentes (Haversine).

---

## 📂 Estructura del Repositorio

```
data-intelligence-platform/
├── README.md                         # Este documento
├── LICENSE                           # MIT
├── .env.example                      # Plantilla de variables de entorno
├── .gitignore                        # Reglas de exclusión
├── .dockerignore                     # Reglas para imágenes Docker
├── pyproject.toml                    # Configuración unificada (ruff, mypy, pytest)
├── requirements.txt                  # Dependencias de runtime
├── requirements-dev.txt              # Dependencias de desarrollo
├── requirements.lock.txt             # Versiones exactas instaladas
├── Makefile                          # Tareas unificadas del proyecto
│
├── architecture/                     # Diseño de la arquitectura
│   ├── system-architecture.md
│   ├── data-flow.md
│   ├── bronze-silver-gold.md
│   ├── data-model.md
│   └── diagrams/
│
├── data/                             # Data Lake local (git-ignored)
│   ├── raw/                          # Archivos originales, sin modificar
│   ├── bronze/                       # Datos estructurados con fidelidad al origen
│   ├── silver/                       # Datos limpios y enriquecidos
│   ├── gold/                         # Data Marts listos para consumo
│   ├── quarantine/                   # Registros rechazados por Quality Gates
│   └── metadata/                     # Metadatos de ingestion runs
│
├── ingestion/                        # Scripts de adquisición
│   ├── maritime/                     # NOAA AIS, Vessel Tracks, Transit Counts
│   ├── ports/                        # World Port Index
│   └── weather/                      # Fuentes meteorológicas
│
├── src/                              # Código fuente modular
│   ├── config.py                     # Configuración tipada con Pydantic
│   ├── logging_config.py             # Logging estructurado
│   ├── storage/                      # db.py, s3_lake.py, bronze_writer.py
│   ├── validation/                   # Quality Gates 1, 2 y 3
│   ├── geospatial/                   # Geofencing y H3
│   ├── tracking/                     # Reconstrucción de trayectorias
│   ├── features/                     # Ingeniería de variables para ML
│   └── ml/                           # Entrenamiento y evaluación
│
├── airflow/                          # Orquestador
│   ├── dags/                         # dag_01_*, dag_02_*, etc.
│   ├── plugins/                      # Operadores personalizados
│   ├── Dockerfile                    # Imagen personalizada con dbt en venv aislado
│   └── requirements.txt              # Dependencias del contenedor
│
├── dbt/maritime/                     # Transformaciones analíticas
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── macros/
│   │   └── generate_schema_name.sql  # Override del prefijado automático
│   ├── models/
│   │   ├── staging/                  # Capa Silver: normalización
│   │   │   ├── _sources.yml
│   │   │   ├── stg_ais_position.sql
│   │   │   └── stg_ais_position.yml
│   │   ├── intermediate/             # Capa Silver: enriquecimiento
│   │   │   ├── int_vessel_position_deltas.sql
│   │   │   ├── int_vessel_tracks.sql
│   │   │   └── schema.yml
│   │   └── marts/                    # Capa Gold: Data Marts
│   │       ├── core/
│   │       ├── port_operations/
│   │       ├── port_congestion/
│   │       ├── vessel_intelligence/
│   │       ├── route_intelligence/
│   │       └── anomaly/
│   ├── snapshots/
│   ├── tests/
│   └── seeds/
│
├── api/                              # API REST con FastAPI
│   └── app/
│       ├── main.py
│       ├── routers/
│       └── schemas/
│
├── ml/                               # Machine Learning
│   ├── training/
│   ├── evaluation/
│   └── models/
│
├── intelligence/                     # Capa de inteligencia generativa
│   ├── prompts/
│   ├── schemas/
│   └── gemini/
│
├── docker/                           # Stack de desarrollo local
│   ├── docker-compose.yml
│   ├── postgres/init/                # 01_create_databases.sql · 02_bronze_quarantine_metadata.sql
│   └── minio/
│
├── scripts/                          # Automatización
│   ├── bootstrap.sh
│   ├── check_environment.sh
│   └── seed_data.sh
│
├── tests/                            # Testing en tres niveles
│   ├── unit/
│   ├── integration/
│   └── data_quality/
│
├── postman/                          # Colección de pruebas de la API
├── dashboards/                       # Visualizaciones
├── monitoring/                       # Configuración de observabilidad
└── docs/                             # Documentación transversal
    ├── decisions/                    # Architecture Decision Records (ADR)
    ├── incidents/                    # Registro de incidentes
    ├── experiments/                  # Experimentos y benchmarks
    └── cost-optimization/            # Análisis de costos cloud
```

---

## 🚀 Guía de Inicio Rápido

### Pre-requisitos

- **Fedora Linux** 40+ (o cualquier distribución con Docker Engine moderno).
- **Docker Engine** ≥ 24 con **Docker Compose v2**.
- **Python** ≥ 3.11 (probado en 3.14).
- **Git** con SSH configurado contra GitHub.
- **dbt-postgres** en un virtualenv aislado (`~/.venvs/dbt`) expuesto en `~/.local/bin/dbt`.
- **make**, **jq**, **curl** disponibles en el sistema.

### Paso 1 — Clonar y preparar el entorno

```bash
git clone git@github.com:kleyber8/data-intelligence-platform.git
cd data-intelligence-platform

cp .env.example .env

# Generar la FERNET_KEY para Airflow y pegarla en .env
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Añadir el UID del usuario para que los archivos del contenedor
# pertenezcan al usuario del host
echo "AIRFLOW_UID=$(id -u)" >> .env
```

### Paso 2 — Crear el entorno virtual e instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt
```

### Paso 3 — Levantar el stack completo

```bash
cd docker
docker compose --env-file ../.env up -d --build
```

La primera ejecución descarga las imágenes base (~1.5 GB) y construye la imagen de Airflow con dbt en venv aislado. Tarda entre 5 y 15 minutos según la conexión. Las ejecuciones posteriores son casi instantáneas.

### Paso 4 — Verificar que todo está operativo

```bash
docker compose --env-file ../.env ps

curl -s http://localhost:8080/health | jq .
curl -s http://localhost:9000/minio/health/live -o /dev/null -w "MinIO: HTTP %{http_code}\n"
docker exec dip-project-postgres psql -U maritime_user -d maritime -c "\dn"

# Verificar que dbt está disponible dentro del contenedor
docker exec dip-airflow-webserver dbt --version
```

Salida esperada:
- Contenedores `dip-project-postgres`, `dip-airflow-postgres`, `dip-minio`, `dip-airflow-webserver`, `dip-airflow-scheduler` en estado `healthy`.
- Airflow responde `{"metadatabase": {"status": "healthy"}, "scheduler": {"status": "healthy"}}`.
- MinIO responde `HTTP 200`.
- PostgreSQL lista los esquemas `bronze`, `silver`, `gold`, `metadata`, `quarantine`, `public`.
- dbt responde con su versión (`Core: 1.8.x · Plugins: postgres 1.8.x`).

### Paso 5 — Verificar la conexión de dbt

```bash
cd dbt/maritime
export DBT_PROFILES_DIR=~/.dbt
set -a; source ../../.env; set +a

dbt debug
```

Salida esperada: **`All checks passed!`**

### Paso 6 — Ejecutar el pipeline completo (Fases 2 y 3)

**Opción A — Disparar desde la CLI (ideal para depuración):**

```bash
cd ~/Projects/data-intelligence-platform
source .venv/bin/activate
set -a; source .env; set +a

# --- FASE 2: Ingestión + Bronze + QG1 ---
python -m ingestion.maritime.noaa_ais --source synthetic

export RUN_ID=$(docker exec dip-project-postgres psql -U maritime_user -d maritime -t -A -c "SELECT ingestion_run_id FROM metadata.ingestion_runs ORDER BY created_at DESC LIMIT 1")
echo "RUN_ID: $RUN_ID"

python -c "from src.storage.bronze_writer import write_bronze_from_landing, count_bronze_rows; rid='$RUN_ID'; print('Bronze:', write_bronze_from_landing(rid)); print('Count:', count_bronze_rows(rid))"
python -c "from src.validation.quality_gate_1 import run_quality_gate_1; print(run_quality_gate_1('$RUN_ID'))"

# --- FASE 3: Silver con dbt + QG2 ---
cd dbt/maritime
export DBT_PROFILES_DIR=~/.dbt

dbt deps
dbt run --select tag:silver --no-version-check
dbt test --select tag:silver --no-version-check

cd ~/Projects/data-intelligence-platform
python -c "from src.validation.quality_gate_2 import run_quality_gate_2; import json; print(json.dumps(run_quality_gate_2(), indent=2, default=str))"
```

**Opción B — Disparar desde Airflow (valida la orquestación completa):**

```bash
# DAG 01 (Bronze)
docker exec dip-airflow-webserver airflow dags unpause dag_01_discovery_ingestion
docker exec dip-airflow-webserver airflow dags trigger dag_01_discovery_ingestion

# DAG 02 (Silver) — después de que DAG 01 termine
docker exec dip-airflow-webserver airflow dags unpause dag_02_silver_transformation
docker exec dip-airflow-webserver airflow dags trigger dag_02_silver_transformation

# Estado de los runs
docker exec dip-airflow-webserver airflow dags list-runs -d dag_01_discovery_ingestion 2>/dev/null | head -3
docker exec dip-airflow-webserver airflow dags list-runs -d dag_02_silver_transformation 2>/dev/null | head -3
```

Interfaz web en `http://localhost:8080` (usuario `admin` / contraseña `admin`) → **DAGs → Graph**.

### Paso 7 — Verificar los resultados en PostgreSQL

```bash
export RUN_ID=$(docker exec dip-project-postgres psql -U maritime_user -d maritime -t -A -c "SELECT ingestion_run_id FROM metadata.ingestion_runs ORDER BY created_at DESC LIMIT 1")

# --- Fase 2 ---
docker exec dip-project-postgres psql -U maritime_user -d maritime -c "
    SELECT quality_status, COUNT(*) FROM bronze.bronze_ais_position
    WHERE ingestion_run_id = '$RUN_ID' GROUP BY quality_status;"

docker exec dip-project-postgres psql -U maritime_user -d maritime -c "
    SELECT quality_rule, COUNT(*) FROM quarantine.quarantine_records
    WHERE ingestion_run_id = '$RUN_ID' GROUP BY quality_rule ORDER BY 2 DESC;"

# --- Fase 3 ---
docker exec dip-project-postgres psql -U maritime_user -d maritime -c "
    SELECT table_schema, table_name, table_type
    FROM information_schema.tables
    WHERE table_schema = 'silver'
    ORDER BY table_name;"

for t in stg_ais_position int_vessel_position_deltas int_vessel_tracks; do
    docker exec dip-project-postgres psql -U maritime_user -d maritime -t -c "SELECT '$t', COUNT(*) FROM silver.$t;"
done

# Muestra de tracks reconstruidos
docker exec dip-project-postgres psql -U maritime_user -d maritime -c "
    SELECT track_id, mmsi, position_ts,
           ROUND(distance_km::numeric, 3) AS distance_km,
           ROUND(calculated_speed_knots::numeric, 2) AS speed_knots,
           is_speed_anomaly
    FROM silver.int_vessel_tracks
    WHERE distance_km IS NOT NULL AND distance_km > 0
    ORDER BY track_id, position_ts
    LIMIT 10;"
```

### Interfaces disponibles tras el arranque

| Servicio | URL | Credenciales |
|---|---|---|
| **Airflow Webserver** | http://localhost:8080 | `admin` / `admin` |
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin` |
| **PostgreSQL proyecto** | `localhost:5432` | `maritime_user` / `change_me_dev_only` |
| **PostgreSQL Airflow** | `localhost:5433` | `airflow` / `change_me_dev_only` |

---

## 🎯 Estrategia de Calidad y Gobernanza

La plataforma implementa una **triple barrera de calidad** que intercepta problemas en tres puntos críticos del flujo:

### Quality Gate 1 — Integridad estructural (post-Bronze) · ✅ implementado

Aplica 6 reglas: `valid_mmsi_present`, `valid_mmsi_format`, `valid_latitude`, `valid_longitude`, `valid_speed`, `valid_timestamp`. Los registros que pasan quedan con `quality_status='validated'`; los que fallan pasan a `quality_status='quarantined'` y se replican en `quarantine.quarantine_records` con el payload JSONB completo y la lista de reglas violadas.

### Quality Gate 2 — Integridad analítica (post-Silver) · ✅ implementado

Aplica 3 reglas sobre las vistas Silver:
- **`referential_consistency`** — cuenta los `ingestion_row_id` huérfanos entre `int_vessel_tracks` y `stg_ais_position`.
- **`temporal_continuity`** — cuenta duplicados de `(mmsi, position_ts)` y deltas temporales negativos.
- **`spatial_continuity`** — cuenta velocidades calculadas mayores a 60 nudos.

Devuelve un diccionario con `all_passed`, `total_violations` y el detalle por regla. En la corrida de verificación: **0 violaciones**.

### Quality Gate 3 — Calidad analítica (post-Gold) · 🚧 próxima fase

Validará completitud, freshness, consistencia, duplicación, valores extremos, calidad de métricas y **ausencia de data leakage** en features de ML.

### Automatización de calidad

- **Ruff** — linter y formateador ultrarrápido, configurado en `pyproject.toml`.
- **mypy** — verificación estática de tipos, con `disallow_untyped_defs = true`.
- **pytest** — framework de testing con marcadores por tipo (`unit`, `integration`, `data_quality`, `slow`).
- **pre-commit** — hooks automáticos que ejecutan todas las verificaciones antes de cada commit.
- **dbt tests** — tests declarativos sobre los modelos (17 tests en Silver).

Con pre-commit y los Quality Gates activos, es imposible que un dato inválido llegue a Gold, y es imposible commitear código que no pase Ruff, mypy y los tests.

---

## 🗺️ Hoja de Ruta

### ✅ Completado — Fase 1 (Bootstrap)

- [x] Estructura modular del repositorio y Data Lake local estandarizado.
- [x] Stack Docker orquestado con aislamiento de redes y volúmenes.
- [x] Configuración tipada con Pydantic Settings.
- [x] Proyecto dbt configurado con perfiles dinámicos por variables de entorno.
- [x] Calidad de código: Ruff, mypy, pytest, pre-commit.
- [x] Control de secretos y `.gitignore` validado.

### ✅ Completado — Fase 2 (Ingestión, Bronze y QG1)

- [x] Extractor de AIS con Polars: sintético o NOAA real · checksum SHA-256 · Parquet Zstd.
- [x] Preservación en Data Lake local particionado tipo Hive (`year=/month=/day=/`).
- [x] Subida automática a MinIO S3 con cliente boto3.
- [x] Registro de metadatos en `metadata.ingestion_runs`.
- [x] Escritor de Bronze con auditoría completa.
- [x] Quality Gate 1 con 6 reglas estructurales.
- [x] Cuarentena con payload JSONB completo y reglas violadas.
- [x] DAG de Airflow `dag_01_discovery_ingestion` con 5 tareas en TaskFlow API.
- [x] Verificación end-to-end: 200 procesados · 170 validados · 30 en cuarentena.

### ✅ Completado — Fase 3 (Capa Silver, dbt y QG2)

- [x] Macro `generate_schema_name` para evitar prefijado `silver_silver`.
- [x] Modelo `stg_ais_position` con normalización y filtrado por validados.
- [x] Modelo `int_vessel_position_deltas` con Haversine en SQL y detección de anomalías.
- [x] Modelo `int_vessel_tracks` con segmentación por gaps de 2 horas.
- [x] 17 tests dbt declarativos en verde (`PASS=17 ERROR=0 WARN=0`).
- [x] Quality Gate 2 con tres reglas analíticas · 0 violaciones.
- [x] DAG `dag_02_silver_transformation` con 5 tareas (TaskFlow + BashOperator).
- [x] dbt en venv aislado dentro del contenedor de Airflow (`/opt/dbt-venv`).
- [x] Datos sintéticos con trayectorias físicamente coherentes.

### 🚧 Próximos hitos — Fase 4 (Capa Gold)

- [ ] Modelo `fact_vessel_voyage` — viajes agregados a partir de tracks.
- [ ] Modelo `dim_port` — dimensión de puertos con geofencing.
- [ ] Modelo `agg_port_operations` — métricas operativas por puerto y periodo.
- [ ] Modelo `agg_port_congestion` — índice de congestión portuaria.
- [ ] Modelo `vessel_intelligence` — perfil operativo por embarcación.
- [ ] Modelo `route_intelligence` — análisis de rutas origen-destino.
- [ ] Modelo `anomaly_mart` — consolidación de anomalías detectadas.
- [ ] Quality Gate 3 — validación analítica sobre Gold.
- [ ] DAG `dag_03_gold_marts` que orqueste `dbt run --select tag:gold`.

### 🔮 Capacidad de extensión — Fases posteriores

- [ ] **Fase 5 (API REST)** — endpoints en FastAPI: `/health`, `/ports`, `/vessels`, `/routes`, `/anomalies`.
- [ ] **Fase 6 (Machine Learning)** — primer modelo de predicción de ETA o forecasting de congestión.
- [ ] **Fase 7 (Intelligence)** — generación de briefings operacionales con Gemini.
- [ ] **Fase 8 (CI/CD)** — pipelines con GitHub Actions: lint, tests, dbt compile, Docker build.
- [ ] **Fase 9 (Cloud)** — integración con AWS S3, IAM, Lambda, CloudWatch.
- [ ] **Fase 10 (IaC)** — infraestructura como código con Terraform.
- [ ] **Fase 11 (Snowflake)** — plataforma analítica cloud y comparación de arquitecturas.

**La arquitectura está preparada para incorporar nuevos dominios sin rediseño**: datos meteorológicos, financieros, urbanos, ambientales, científicos, gubernamentales, deportivos, industriales, o cualquier fuente pública o privada que aporte valor a la comunidad. El caso marítimo es la primera prueba, no la frontera conceptual.

---

## 🤝 Contribución

Este proyecto está concebido como un **espacio abierto de aprendizaje y experimentación**. Cualquier persona —estudiante, docente, investigador, profesional— puede contribuir. Las contribuciones no se limitan al código:

- **Código:** nuevas fuentes de datos, modelos dbt, DAGs, endpoints de API, features de ML.
- **Documentación:** explicaciones, tutoriales, traducciones, corrección de errores.
- **Investigación:** comparaciones metodológicas, validación de resultados, benchmarks.
- **Testing:** casos de prueba, edge cases, validación de calidad.
- **Diseño:** diagramas, visualizaciones, mejoras de arquitectura.
- **Análisis estadístico:** estudio de patrones, validación de supuestos, interpretación.

**Flujo de contribución:**

1. Abre un *issue* describiendo la contribución propuesta antes de empezar a trabajar.
2. Haz un *fork* del repositorio y crea una rama descriptiva (`feat/nueva-fuente`, `docs/mejora-adr`).
3. Sigue las convenciones del proyecto: type hints, tests, documentación de decisiones.
4. Abre un *pull request* describiendo qué problema resuelve, cómo se implementa y por qué se hizo de esa forma.

Cada decisión técnica relevante debe documentarse bajo el esquema:

> **problema → alternativas → decisión → justificación → consecuencias → mejoras futuras**

---

## 📄 Licencia

Este proyecto se distribuye bajo la **Licencia MIT**. Puedes usar, modificar, distribuir y reutilizar el código libremente, con el único requisito de preservar la atribución original. Ver [`LICENSE`](./LICENSE) para el texto completo.

---

<div align="center">

**Data Intelligence Platform** · Fase 3 · Capa Silver y dbt completados

*Construido con rigor, documentado con honestidad, abierto a quien quiera aprender.*

</div>
