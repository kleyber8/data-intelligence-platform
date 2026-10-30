# 📊 Estado de Avance: Radiografía Técnica de las 6 Fases

Este documento detalla la implementación y validación técnica de las 6 fases completadas. No es teoría; es el registro de un ecosistema local *end-to-end* operativo, validado con Quality Gates, pruebas automatizadas y métricas de ejecución.

## 🏗️ Fase 1: Bootstrap e Infraestructura
**Objetivo:** Levantar un entorno reproducible y aislado.
*   **Stack:** Docker Compose, PostgreSQL 16, Airflow 2.10.2, MinIO, dbt 1.12.
*   **Hitos logrados:**
    *   Creación de la red bridge interna (`docker_default`) y volúmenes persistentes.
    *   Configuración de 6 esquemas estructurales (`bronze`, `silver`, `gold`, `metadata`, `quarantine`, `public`).
    *   Aislamiento de variables de entorno y secretos (`.env` vs `.env.example`).
    *   Implementación de Healthchecks y contenedores sin privilegios de root.

## 🥉 Fase 2: Ingestión y Capa Bronze
**Objetivo:** Ingesta inmutable y validación estructural inicial (QG1).
*   **Stack:** Python, Polars, SQLAlchemy, MinIO S3.
*   **Hitos logrados:**
    *   Extractor de AIS (sintético y NOAA) con cálculo de checksum SHA-256.
    *   Preservación en Data Lake local con formato Parquet (Zstd) y particionado Hive.
    *   Inserción en tabla `bronze.bronze_ais_position` con inyección de auditoría (`ingestion_run_id`).
*   **Métricas de Validación:**
    *   **QG1:** 200 registros procesados → **170 validados** (85%) y **30 en cuarentena** (15%).
    *   Los 30 rechazos se aislaron con payload JSONB en `quarantine.quarantine_records`.
    *   Las 6 reglas del QG1 (MMSI, coordenadas, velocidad, timestamp) funcionaron correctamente.

## 🥈 Fase 3: Capa Silver y Transformaciones dbt
**Objetivo:** Normalización, reconstrucción de trayectorias y Quality Gate 2.
*   **Stack:** dbt 1.12, PostgreSQL, BashOperator (Airflow).
*   **Hitos logrados:**
    *   Creación del modelo staging `stg_ais_position`.
    *   Implementación de la **Fórmula de Haversine en SQL** para distancia geodésica (`int_vessel_position_deltas`).
    *   Segmentación de trayectorias basada en gaps de 2 horas (`int_vessel_tracks`).
    *   Aislamiento de dbt en venv (`/opt/dbt-venv`) dentro de Airflow para evitar conflictos de dependencias.
*   **Métricas de Validación:**
    *   **17 tests dbt** ejecutados en verde (`PASS=17`, `ERROR=0`).
    *   **QG2:** 0 violaciones en integridad referencial, continuidad temporal y espacial.

## 🥇 Fase 4: Capa Gold, Data Marts y RBAC
**Objetivo:** Modelado dimensional analítico y endurecimiento de seguridad.
*   **Stack:** dbt, PostgreSQL, SQL (DDL).
*   **Hitos logrados:**
    *   Creación de **7 Data Marts**: `fact_vessel_voyage`, `dim_port`, `agg_port_operations`, `agg_port_congestion`, `vessel_intelligence`, `route_intelligence` y `anomaly_mart`.
    *   Implementación de **RBAC (Least Privilege)** con 4 usuarios: `pipeline_user`, `dbt_user`, `api_user`, `analyst_user`.
*   **Métricas de Validación:**
    *   **35 tests dbt** ejecutados en verde.
    *   **QG3:** 0 violaciones. Validación Cross-Layer (suma de distancias Gold vs Silver) exitosa.
    *   **Prueba de RBAC:** `api_user` puede leer Gold, pero PostgreSQL le deniega el acceso a Silver (`permission denied for schema silver`).

## 🧠 Fase 5: Rigor Matemático y Preparación de ML
**Objetivo:** Suavizado de trayectorias, resampling y auditoría estadística.
*   **Stack:** Python, NumPy, SciPy, Polars.
*   **Hitos logrados:**
    *   Módulo de auditoría de sesgo (`quarantine_audit.py`) usando Chi-cuadrado e Índice de Gini.
    *   Resampling temporal a malla de 15 minutos (`temporal_resampling.py`).
    *   **Filtro de Kalman 4D** (`kalman_filter.py`) para suavizar ruido GPS en coordenadas y velocidad.
    *   Pipeline de preparación de features (`feature_prep.py`) con split temporal estricto (Train 70%, Val 15%, Test 15%).
*   **Métricas de Validación:**
    *   **Auditoría:** Chi² = 5.63 (p=0.344, distribución uniforme, sin sesgo). Gini = 0.152.
    *   **Kalman:** RMSE de latitud/longitud ≈ 0.06 mm (dataset sintético perfecto, sin ruido).
    *   **Resampling:** 96.7% de datos interpolados (malla más densa que los pings originales).

## 🔌 Fase 6: API REST de Consumo con FastAPI
**Objetivo:** Exponer la capa Gold con seguridad, validación y alto rendimiento.
*   **Stack:** FastAPI, Uvicorn, Pydantic, SQLAlchemy Async, JWT.
*   **Hitos logrados:**
    *   Arquitectura modular: routers por dominio (`ports`, `vessels`, `routes`, `anomalies`).
    *   Conexión a base de datos aislada usando exclusivamente `api_user`.
    *   Seguridad: JWT con expiración de 30 minutos, Rate Limiting con slowapi y CORS.
    *   Documentación automática con Swagger UI interactivo.
*   **Métricas de Validación:**
    *   **4 tests de Pytest** en verde: healthcheck, login (JWT), rechazo 401 sin token y aceptación 200 con token.
    *   Endpoints operativos y consultando datos reales de la base de datos.

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
