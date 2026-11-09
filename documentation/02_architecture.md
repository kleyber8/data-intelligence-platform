# 🏛️ Arquitectura de Referencia y Stack Tecnológico Completo

La plataforma implementa una arquitectura analítica moderna basada en el **Patrón Medallion**, orquestada de extremo a extremo. El diseño garantiza el desacoplamiento de responsabilidades, la inmutabilidad del dato original y una estricta separación entre las fases de transformación y consumo.

## 1. Topología del Flujo de Datos

El pipeline sigue una topología de capas progresivas. Cada transición crítica está bloqueada por un *Quality Gate* que actúa como contrato de datos:

```text
[ FUENTES DE DATOS ] (NOAA AIS diario real, WPI vía espejo Hugging Face)
          │
          ▼
[ INGESTIÓN (Python + Polars Lazy API) ] ──> Idempotencia: validación por source_url + checksum SHA-256
          │
          ▼
[ LANDING / DATA LAKE ] (MinIO Local / AWS S3 Cloud) ──> Particionado Hive (Zstd, streaming)
          │
          ▼
[ BRONZE (PostgreSQL) ] ──> COPY masivo (synchronous_commit = OFF) + Auditoría
          │
    [ 🛡️ QUALITY GATE 1 ] (Validación de tipos, nulos y rangos físicos)
          │
          ▼
[ SILVER (dbt + PostgreSQL) ] ──> Normalización, Enriquecimiento (Haversine, Tracks)
          │
    [ 🛡️ QUALITY GATE 2 ] (Integridad referencial y continuidad temporal, tolerancia 1%)
          │
          ▼
[ GOLD (dbt + PostgreSQL) ] ──> Modelado Dimensional (3,804 Puertos reales, 7 Data Marts)
          │
    [ 🛡️ QUALITY GATE 3 ] (Consistencia cross-layer y ausencia de data leakage)
          │
          ▼
[ CAPA DE CONSUMO ]
    ┌──────────────┬───────────────┬─────────────────────┐
    │              │               │                     │
[ API REST ]   [ MLOps / XGBoost ] [ LLMs (Gemini) ]
(FastAPI)      (MinIO Model Reg.)  (Generative Briefings)
    │              │               │
    └──────────────┴───────────────┘
```

### 1.1. Nota de Diseño: Cargas Masivas en la Ingesta (Lazy API + COPY)

La ingesta ya no opera sobre muestras sintéticas: procesa el **archivo diario real de NOAA AIS (8.1 millones de filas)**. Esto exigió dos decisiones de ingeniería explícitas en la capa de ingesta:

*   **Lazy API de Polars (`scan_csv` → `sink_parquet`):** El CSV diario de NOAA no cabe cómodamente en RAM. En lugar de `read_csv` (eager), la ingesta usa el motor de streaming de Polars: `scan_csv` materializa el plan de ejecución y `sink_parquet` escribe el Parquet de forma incremental en streaming. Resultado: transformación de un archivo de gigabytes con consumo de memoria volátil constante, independiente del tamaño del archivo.
*   **COPY masivo de `psycopg2`:** La escritura en `bronze.bronze_ais_position` no usa `INSERT` fila a fila (u `executemany`, insostenible con millones de filas). Se cargan lotes de 250,000 filas por cada llamada al COPY con `SET LOCAL synchronous_commit = OFF` y `maintenance_work_mem = '512MB'`, dentro de una transacción única: el `fsync` interior la ejecuta el `checkpointer` de PostgreSQL, no cada `INSERT`. La carga de 8.1M de filas termina en segundos, no en minutos.
*   **Idempotencia antes de escribir:** Antes de la descarga, el módulo consulta `metadata.ingestion_runs` por `source_url` (1 URL ⇔ 1 archivo diario) y después de descargar, por checksum SHA-256 del ZIP de origen. Si el archivo ya fue procesado (`landed → completed`), la ingesta devuelve `already_processed` y el DAG 01 omite la escritura en Bronze y el QG1 sin fallar.

## 2. Stack Tecnológico y Justificación Arquitectónica

La elección de herramientas responde a criterios de escalabilidad, robustez, mantenibilidad y al principio rector **Local-First + Cloud-Where-Useful**.

| Componente | Herramienta / Fase | Rol Arquitectónico y Justificación Técnica |
| :--- | :--- | :--- |
| **Orquestación** | Apache Airflow 2.10.2 | Coordina dependencias complejas mediante DAGs con la *TaskFlow API*. Monitorea reintentos, SLAs y re-enlaces (sensors) de producción: DAG 01 es idempotente y DAG 03 espera al QG2 de DAG 02 con `ExternalTaskSensor`. |
| **Ingesta y Datos** | Python 3.14 + Polars | Polars (Rust): la **Lazy API** (`scan_csv` + `sink_parquet`) procesa archivos diarios de gigabytes en streaming, con consumo de RAM constante independiente del tamaño del archivo. |
| **Carga a Bronze** | `psycopg2` (COPY masivo) | Escritura por lotes de 250,000 filas con `SET LOCAL synchronous_commit = OFF` y `maintenance_work_mem` elevado. Es la estrategia de carga usada tanto para AIS (8.1M filas) como para los puertos (TRUNCATE + COPY atómico). |
| **Fuentes Externas** | Hugging Face (espejo CSV) | La API REST de ArcGIS (World Port Index NGA) se reemplazó por un espejo CSV estable: carga de 3,804 **puertos reales** en `bronze.bronze_ports` con `TRUNCATE` previo en la misma transacción (sin dependencia de WAF). |
| **Web Scraping / WAF** | `curl_cffi` | Legado de la Fase 7 (impersonación de huella TLS Chrome 110 contra el WAF de ArcGIS). Se mantiene en el stack por compatibilidad, pero la ingesta de puertos activa hoy es el espejo de Hugging Face. |
| **Transformación** | dbt (Data Build Tool) 1.12 | Aplica lógica de negocio SQL (ELT). Utiliza tests declarativos para validar contratos de datos en Silver y Gold, con `post-hooks` de índices en Silver y tolerancia del 1% en el QG2 para el ruido real de los GPS marinos. |
| **Base de Datos Core** | PostgreSQL 16 | Almacén relacional estructurado en esquemas físicos (`bronze`, `silver`, `gold`). Uso intensivo de JSONB para cuarentena. Índices de soporte en Bronze (`mmsi`, `position_ts`, `quality_status`) y Silver (`track_id + position_ts`, índices parciales para anomalías). |
| **Data Lake** | MinIO (Local) / AWS S3 | Emulador S3 local que garantiza portabilidad. En cloud se usa S3 con cifrado KMS y particionado Hive. |
| **Consumo API** | FastAPI + Pydantic | API REST asíncrona de alto rendimiento. Validación estricta de esquemas y documentación OpenAPI automática. |
| **Seguridad API** | JWT + OAuth2 + slowapi | Autenticación basada en tokens de corta duración (30m) y protección contra ataques DoS mediante Rate Limiting. |
| **Machine Learning** | XGBoost + Scikit-Learn | Modelos predictivos de ETA (Regresión) y detección de anomalías. Uso de PCA y ANOVA para selección de features. |
| **Rigor Causal** | `statsmodels` (Granger) | Validación de relaciones predictivas temporales (Causalidad de Granger) para evitar falacias de correlación. |
| **MLOps Registry** | MinIO + Joblib | Serialización y versionado de modelos (`.joblib`) en buckets S3 para su consumo dinámico en la API. |
| **Inteligencia LLM** | Google Gemini API | Generación de *briefings* operacionales. Se alimenta solo de eventos estructurados de Gold para evitar alucinaciones. |
| **Cloud Infra** | AWS (IAM, Lambda, CloudWatch) | Fase de despliegue productivo. Uso de roles (IAM) y procesamiento serverless para eventos específicos. |
| **Secrets Management**| AWS Secrets Manager | Eliminación de `.env` en producción. Rotación automática de credenciales de bases de datos y APIs. |
| **Infra as Code** | Terraform | (Fase 11) Aprovisionamiento declarativo de toda la infraestructura AWS. Versionado y auditable. |
| **CI/CD** | GitHub Actions | Automatización de linting, pruebas (pytest), compilación dbt y construcción de imágenes Docker en cada push. |
| **Data Warehouse** | Snowflake | (Fase 12) Migración analítica Cloud. Se evaluará el uso de Streams+Tasks o Dynamic Tables vs Airflow+dbt. |

## 3. Las Capas del Medallion en Detalle

### 3.1. Landing (Data Lake Inmutable)
*   **Formato:** Parquet comprimido con Zstd (alta tasa de compresión, lectura columnar rápida).
*   **Estructura:** Particionado Hive (`raw/maritime/year=YYYY/month=MM/day=DD/`) para optimizar consultas.
*   **Inmutabilidad:** Los archivos originales nunca se alteran. Se calcula su SHA-256 (sobre el ZIP de NOAA, archivo origen determinista) en la ingesta para auditoría e idempotencia.
*   **Streaming:** El CSV del diario NOAA se procesa con `scan_csv` + `sink_parquet` (Lazy API de Polars), extrayendo y normalizando las 10 columnas de negocio sin materializar el dataset en RAM.

### 3.2. Capa Bronze (Fidelidad Estructural)
*   **Propósito:** Preservar la estructura original sin aplicar reglas de negocio.
*   **Transformación:** Cero. Solo se inyectan columnas de auditoría (`ingestion_run_id`, `ingestion_row_id`, `created_at`).
*   **Carga Masiva:** `psycopg2.COPY` con chunks de 250,000 filas y `SET LOCAL synchronous_commit = OFF`. En puertos: `TRUNCATE` + `COPY` en la misma transacción (replace atómico compatible con `bronze_ports`).
*   **Idempotencia:** El run registra su ciclo de vida en `metadata.ingestion_runs` (`landed` al aterrizar el Parquet, `completed` tras el COPY exitoso). Re-ejecutar el DAG nunca duplica filas.
*   **Estructura:** Tablas relacionales en PostgreSQL con índices de soporte (`ingestion_run_id`, `mmsi`, `position_ts DESC`, `quality_status`).

### 3.3. Capa Silver (Normalización y Enriquecimiento)
*   **Propósito:** Limpieza y reconstrucción de entidades complejas sobre datos reales (8.1M posiciones).
*   **Transformación:** Filtrado de validados, casteo estricto, cálculo de distancia geodésica (Fórmula de Haversine) y segmentación con ventanas (`LAG`/`LEAD`) para reconstruir tracks a 2 horas de corte.
*   **Materialización:** **Tablas físicas (`table`)** con `post-hooks` de índices (`(mmsi, position_ts)`, `(ingestion_row_id)`, `(track_id, position_ts)` y parcial sobre `is_speed_anomaly`). La decisión de migrar de `view` a `table` respondió a la resolución de deadlocks en dbt y a la necesidad de planes de ejecución con índices cuando el volumen pasó de escalar sintético a producción.

### 3.4. Capa Gold (Modelado para Consumo)
*   **Propósito:** Datos listos para dashboards, ML y API.
*   **Transformación:** Data Marts (ej. `fact_vessel_voyage`, `agg_port_congestion`, `dim_port` con **3,804 puertos reales** del World Port Index cargados vía espejo Hugging Face → `int_ports` → `dim_port`).
*   **Materialización:** Tablas físicas (Tables) con build atómico de dbt (sin `--full-refresh` diario) para garantizar latencia cero en las consultas de la API.

## 4. La Triple Barrera de Calidad (Quality Gates)

Los Quality Gates son **barreras de contención**, no validaciones cosméticas:

*   **QG1 (Post-Bronze):** Valida tipos, rangos geográficos y nulos. Los datos corruptos se derivan a `quarantine.quarantine_records` (JSONB) en lugar de descartarse, permitiendo auditar el error.
*   **QG2 (Post-Silver):** Valida continuidad temporal y espacial con un **threshold de tolerancia del 1%**: con GPS marinos reales, un ruido residual es físicamente esperable, por lo que el gate evalúa el **porcentaje global de violaciones** sobre el total de registros en lugar de bloquear por un único error. Detalles en [Calidad y Gobernanza](./05_quality_governance.md).
*   **QG3 (Post-Gold):** Valida consistencia analítica. Comprueba la suma de distancias Cross-Layer (Gold vs Silver) para evitar errores de agregación y verifica *freshness* antes de exponer los datos a la API.

## 5. Orquestación, Aislamiento y Despliegue

Todo el ecosistema local se levanta mediante `docker-compose.yml`:

*   **Red Bridge Interna:** Los contenedores se comunican por DNS interno (nombres de servicio), no por IPs.
*   **Aislamiento de dbt:** dbt se aísla en su propio virtualenv (`/opt/dbt-venv`) dentro del contenedor para evitar conflictos de dependencias (ej. versiones de SQLAlchemy).
*   **Dependencias entre Capas en Producción:** DAG 03 acopla su ejecución a la finalización del QG2 de DAG 02 mediante `ExternalTaskSensor` (`mode="reschedule"`), eliminando condiciones de carrera entre las ejecuciones diarias de Silver y Gold.
*   **Seguridad de Red:** Los puertos expuestos al host se limitan a interfaces de administración (Airflow, MinIO, pgAdmin, FastAPI, Portainer).

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
