# 🏛️ Arquitectura de Referencia y Stack Tecnológico Completo

La plataforma implementa una arquitectura analítica moderna basada en el **Patrón Medallion**, orquestada de extremo a extremo. El diseño garantiza el desacoplamiento de responsabilidades, la inmutabilidad del dato original y una estricta separación entre las fases de transformación y consumo.

## 1. Topología del Flujo de Datos

El pipeline sigue una topología de capas progresivas. Cada transición crítica está bloqueada por un *Quality Gate* que actúa como contrato de datos:

```text
[ FUENTES DE DATOS ] (NOAA AIS, APIs Públicas, Sensores)
          │
          ▼
[ INGESTIÓN (Python + Polars) ] ──> Cálculo de checksums SHA-256
          │
          ▼
[ LANDING / DATA LAKE ] (MinIO Local / AWS S3 Cloud) ──> Particionado Hive (Zstd)
          │
          ▼
[ BRONZE (PostgreSQL) ] ──> Fidelidad estructural (Datos crudos + Auditoría)
          │
    [ 🛡️ QUALITY GATE 1 ] (Validación de tipos, nulos y rangos físicos)
          │
          ▼
[ SILVER (dbt + PostgreSQL) ] ──> Normalización, Enriquecimiento (Haversine, Tracks)
          │
    [ 🛡️ QUALITY GATE 2 ] (Integridad referencial y continuidad temporal)
          │
          ▼
[ GOLD (dbt + PostgreSQL/Snowflake) ] ──> Modelado Dimensional y Data Marts
          │
    [ 🛡️ QUALITY GATE 3 ] (Consistencia cross-layer y ausencia de data leakage)
          │
          ▼
[ CAPA DE CONSUMO ] ──> API REST (FastAPI), ML (Scikit-Learn), LLMs (Gemini)
```

## 2. Stack Tecnológico y Justificación Arquitectónica

La elección de herramientas responde a criterios de escalabilidad, robustez, mantenibilidad y al principio rector **Local-First + Cloud-Where-Useful**.

| Componente | Herramienta / Fase | Rol Arquitectónico y Justificación Técnica |
| :--- | :--- | :--- |
| **Orquestación** | Apache Airflow 2.10.2 | Coordina dependencias complejas mediante DAGs con la *TaskFlow API*. Monitorea reintentos y SLAs. |
| **Ingesta y Datos** | Python 3.14 + Polars | Polars (Rust) se usa para extracción y manipulación de datos en memoria con rendimiento superior a Pandas. |
| **Transformación** | dbt (Data Build Tool) 1.12 | Aplica lógica de negocio SQL (ELT). Utiliza tests declarativos para validar contratos de datos en Silver y Gold. |
| **Base de Datos Core** | PostgreSQL 16 | Almacén relacional estructurado en esquemas físicos (`bronze`, `silver`, `gold`). Uso intensivo de JSONB para cuarentena. |
| **Data Lake** | MinIO (Local) / AWS S3 | Emulador S3 local que garantiza portabilidad. En cloud se usa S3 con cifrado KMS y particionado Hive. |
| **Consumo API** | FastAPI + Pydantic | API REST asíncrona de alto rendimiento. Validación estricta de esquemas y documentación OpenAPI automática. |
| **Seguridad API** | JWT + OAuth2 + slowapi | Autenticación basada en tokens de corta duración (30m) y protección contra ataques DoS mediante Rate Limiting. |
| **Machine Learning** | Scikit-Learn + SHAP + SciPy | Modelos predictivos (ETA, Congestión) y detección de anomalías (Isolation Forest). SHAP para explicabilidad. |
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
*   **Inmutabilidad:** Los archivos originales nunca se alteran. Se calcula su SHA-256 en la ingesta para auditoría.

### 3.2. Capa Bronze (Fidelidad Estructural)
*   **Propósito:** Preservar la estructura original sin aplicar reglas de negocio.
*   **Transformación:** Cero. Solo se inyectan columnas de auditoría (`ingestion_run_id`, `ingestion_row_id`, `created_at`).
*   **Estructura:** Tablas relacionales en PostgreSQL.

### 3.3. Capa Silver (Normalización y Enriquecimiento)
*   **Propósito:** Limpieza y reconstrucción de entidades complejas.
*   **Transformación:** Filtrado de validados, casteo estricto, cálculo de distancia geodésica (Fórmula de Haversine) y segmentación con ventanas (`LAG`/`LEAD`) para reconstruir tracks.
*   **Materialización:** Vistas (Views) para mantener el dato ágil y siempre actualizado.

### 3.4. Capa Gold (Modelado para Consumo)
*   **Propósito:** Datos listos para dashboards, ML y API.
*   **Transformación:** Data Marts (ej. `fact_vessel_voyage`, `agg_port_congestion`, `vessel_intelligence`).
*   **Materialización:** Tablas físicas (Tables) para garantizar latencia cero en las consultas de la API.

## 4. La Triple Barrera de Calidad (Quality Gates)

Los Quality Gates son **barreras de contención**, no validaciones cosméticas:

*   **QG1 (Post-Bronze):** Valida tipos, rangos geográficos y nulos. Los datos corruptos se derivan a `quarantine.quarantine_records` (JSONB) en lugar de descartarse, permitiendo auditar el error.
*   **QG2 (Post-Silver):** Valida continuidad temporal y espacial. Bloquea saltos de posición físicamente imposibles (ej. saltos de 2000 nudos) y asegura que los tracks sean coherentes.
*   **QG3 (Post-Gold):** Valida consistencia analítica. Comprueba la suma de distancias Cross-Layer (Gold vs Silver) para evitar errores de agregación y verifica *freshness* antes de exponer los datos a la API.

## 5. Orquestación, Aislamiento y Despliegue

Todo el ecosistema local se levanta mediante `docker-compose.yml`:

*   **Red Bridge Interna:** Los contenedores se comunican por DNS interno (nombres de servicio), no por IPs.
*   **Aislamiento de dbt:** dbt se aísla en su propio virtualenv (`/opt/dbt-venv`) dentro del contenedor para evitar conflictos de dependencias (ej. versiones de SQLAlchemy).
*   **Seguridad de Red:** Los puertos expuestos al host se limitan a interfaces de administración (Airflow, MinIO, pgAdmin, FastAPI, Portainer).

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
