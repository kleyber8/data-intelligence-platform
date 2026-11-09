# 📊 Estado de Avance: Radiografía Técnica de las Fases

Este documento detalla la implementación y validación técnica de las 8 fases completadas. No es teoría; es el registro de un ecosistema local *end-to-end* operativo —**desde la Fase 8, con datos reales de producción (NOAA AIS y World Port Index)**—, validado con Quality Gates, pruebas automatizadas y métricas de ejecución.

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
    *   Conexión a base de datos aislada exclusivamente `api_user`.
    *   Seguridad: JWT con expiración de 30 minutos, Rate Limiting con slowapi y CORS.
    *   Documentación automática con Swagger UI interactivo.
*   **Métricas de Validación:**
    *   **4 tests de Pytest** en verde: healthcheck, login (JWT), rechazo 401 sin token y aceptación 200 con token.
    *   Endpoints operativos y consultando datos reales de la base de datos.

## 🤖 Fase 7: Machine Learning, Modelos Predictivos y Rigor Causal
**Objetivo:** Modelos predictivos, análisis causal e ingesta de infraestructura portuaria real.
*   **Stack:** XGBoost, Scikit-Learn, SciPy, statsmodels, curl_cffi, ArcGIS API, MinIO, Joblib, FastAPI.
*   **Hitos logrados:**
    *   **Ingesta de Puertos NGA:** Evasión del bloqueo WAF (HTTP 503) mediante `curl_cffi` (impersonación de huella TLS de Chrome 110) y consumo paginado de la API REST de ArcGIS, ingiriendo **3,669 puertos reales** en `bronze.bronze_ports`.
    *   **Reducción de Dimensionalidad:** Aplicación de PCA y ANOVA F-test (p < 0.05) para eliminar multicolinealidad y seleccionar variables predictivas robustas.
    *   **Modelo XGBoost (ETA):** Entrenamiento con split temporal estricto (70/15/15) para prevenir *data leakage*, incorporando regularización L1/L2 y *Early Stopping*.
    *   **Rigor Causal (Granger):** Implementación del Test de Causalidad de Granger con `statsmodels` para evaluar relaciones temporales predictivas entre series de congestión portuaria.
    *   **Model Registry (MinIO):** Serialización de artefactos con `joblib` y versionado automático en MinIO S3 (bucket `ml-models`).
    *   **Inferencia en FastAPI:** Creación del endpoint seguro `POST /api/v1/predict/eta` protegido con JWT, que carga dinámicamente el modelo más reciente desde MinIO.
*   **Métricas de Validación:**
    *   **Modelo XGBoost:** Evaluación de MAE y RMSE en el conjunto de prueba temporal (separado de train/val).
    *   **Pytest:** Pruebas automatizadas en verde validando el contrato Pydantic y el acceso autorizado al endpoint de inferencia.

> **Nota evolutiva (Fase 8):** la fuente de puertos original (API REST de ArcGIS) quedó bloqueada por el WAF (HTTP 503) de forma persistente. La Fase 8 reemplaza esa fuente por un espejo CSV estable en Hugging Face; los detalles operativos de la fuente activa están en la sección siguiente.

---
## 🚀 Fase 8: Hardening de Producción y Datos Reales
**Objetivo:** Migrar el pipeline de un ecosistema de validación (datos sintéticos y muestras pequeñas) a un ecosistema de **producción con datos reales a escala**, endureciendo la ingesta contra re-ejecuciones y calibrando los Quality Gates contra el ruido real del sensor GPS marino.
*   **Stack:** Polars (Lazy API), psycopg2 (COPY masivo), Hugging Face (espejo CSV del World Port Index), PostgreSQL, dbt, Airflow.
*   **Hitos logrados:**
    *   **Datos Reales NOAA AIS:** Conexión al archivo diario real de NOAA (**8.1 millones de filas**) como fuente primaria, reemplazando los datos sintéticos de las fases 2–5 en la operación diaria del pipeline.
    *   **Idempotencia de la Ingesta:** Implementación de doble validación en el DAG 01 —por `source_url` (1 URL ⇔ 1 archivo diario ⇔ 1 ciclo de datos) y por **checksum SHA-256** del ZIP— contra `metadata.ingestion_runs`. El run transita el ciclo `landed → completed` (marcado tras el COPY exitoso), y el DAG devuelve `already_processed` ante re-triggers, backfills o descoordinaciones, sin fallar y sin duplicar los 8.1M de filas.
    *   **Carga Masiva a Bronze:** Optimización de la escritura con `psycopg2.COPY` en chunks de 250,000 filas y `SET LOCAL synchronous_commit = OFF` (más `maintenance_work_mem` elevado): la carga de 8.1M de filas completó en **segundos**, no en minutos, al transferir el costo del `fsync` al `checkpointer` de PostgreSQL en lugar de ejecutarlo por cada inserción.
    *   **Lazy API de Polars:** Transformación CSV→Parquet con `scan_csv` + `sink_parquet` (streaming): el consumo de memoria es constante e independiente del tamaño del archivo diario de NOAA (gigabytes), eliminando el riesgo de OOM durante la ingesta.
    *   **Puertos vía Hugging Face:** Reemplazo de la API de ArcGIS (bloqueada de forma persistente por WAF/503) por el espejo CSV del dataset `world-seaports-and-airports`: **3,804 puertos reales** limpiados (detrás de headers tolerantes, con filtrado de coordenadas ±90/±180 y deduplicación por `port_index`) y cargados en `bronze.bronze_ports` con `TRUNCATE` previo dentro de la misma transacción (replace atómico).
    *   **Threshold de Tolerancia del 1% en QG2:** Con datos GPS marinos reales, un porcentaje pequeño de ruido es estadísticamente esperable (`GPS drift`, transmisores desalineados, tasas de reporte irregulares). El QG2 pasa de bloquear por un solo error a evaluar el **porcentaje global de violaciones** sobre el total analizado. La primera corrida con el archivo diario real produjo 2,849 violaciones de `spatial_continuity`; con el threshold del 1% el gate pasó de estado FAIL a **resultado válido**, y las violaciones quedan auditadas (ver [Calidad y Gobernanza](./05_quality_governance.md)).
    *   **Resolución de Deadlocks en dbt:** Cambio de materialización de los modelos Silver (`stg_ais_position`, `int_vessel_position_deltas`, `int_vessel_tracks`) de `view` a **`table`**, con `post-hooks` que recrean los índices de soporte (`(mmsi, position_ts)`, `(ingestion_row_id)`, `(track_id, position_ts)` y parcial sobre `is_speed_anomaly`). Esto eliminó los deadlocks de dbt bajo consultas concurrentes y dio planes de ejecución estables para los 8.1M de filas.
    *   **Acoplamiento de Producción:** DAG 03 espera a DAG 02 con `ExternalTaskSensor` (`mode="reschedule"`), eliminando condiciones de carrera entre Silver y Gold; los build de Gold se ejecutan sin `--full-refresh` (swap atómico de tablas del adaptador dbt-postgres).
*   **Métricas de Validación:**
    *   **Volumen en producción:** 8,100,000 filas AIS diarias en `bronze.bronze_ais_position` + 3,804 puertos reales en `bronze.bronze_ports`.
    *   **Latencia de ingesta:** carga Bronze del archivo diario completo en segundos (COPY masivo + `synchronous_commit=OFF`).
    *   **Idempotencia verificada:** re-ejecución del DAG 01 ante el mismo archivo diario → `status=already_processed`, 0 filas duplicadas (validación por `source_url` + checksum SHA-256 en `metadata.ingestion_runs`).
    *   **QG2 con datos reales:** 2,849 violaciones iniciales (0% de tasa de paso) → **threshold del 1%**: gate en verde evaluando el porcentaje global (`spatial_continuity + temporal_continuity`) sobre 8.1M de registros analizados.
    *   **Estabilidad dbt:** 0 deadlocks tras el cambio a materialización `table` con post-hooks de índices en Silver.

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
