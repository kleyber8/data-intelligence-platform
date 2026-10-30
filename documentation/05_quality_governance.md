# 🎯 Calidad y Gobernanza de Datos

En arquitecturas de datos modernas, la calidad no es un proceso de "revisión al final del pipeline". La calidad y la gobernanza son **contratos de datos** aplicados en cada transición de capa. Un pipeline que mueve datos rápido pero con datos corruptos o no rastreables es un pasivo, no un activo.

## 1. El Linaje Absoluto (Data Lineage)

Cada registro que fluye por la plataforma es auditable hasta su origen físico. Para lograr esto, el pipeline inyecta metadatos de trazabilidad desde la primera línea de código:

*   **`ingestion_run_id` (UUIDv4):** Identifica la corrida completa del pipeline. Permite agrupar todos los registros de una ingesta específica (ej. descarga del 28 de octubre).
*   **`ingestion_row_id` (UUIDv4):** Asignado a cada fila en la capa Bronze. Permite rastrear un registro individual a través de sus transformaciones en Silver y Gold.
*   **`source_file`:** Almacena la ruta del archivo Parquet original en el Data Lake.

**El flujo de trazabilidad:**
`Archivo Parquet en MinIO` → `fila en bronze.bronze_ais_position` → `track_id en silver.int_vessel_tracks` → `fila en gold.fact_vessel_voyage` → `respuesta en FastAPI`.

## 2. La Triple Barrera de Calidad (Quality Gates)

Los Quality Gates (QG) son **barreras de contención**. Si un dato no cumple el contrato, no avanza a la siguiente capa y se registra el motivo.

### 2.1. QG1: Integridad Estructural (Post-Bronze)
Aplica 6 reglas estrictas al momento de ingresar los datos a Bronze.
*   **Reglas:** Validación de presencia de MMSI, formato de 9 dígitos, rangos de latitud/longitud física, límites de velocidad (0-100 nudos) y timestamps no futuros.
*   **Contrato:** 170 registros pasaron la validación (85%). Los 30 inválidos (15%) se derivaron a cuarentena con su payload original en JSONB.

### 2.2. QG2: Integridad Analítica (Post-Silver)
Aplica 3 reglas tras la normalización y reconstrucción de entidades en dbt.
*   **Reglas:** `referential_consistency` (sin registros huérfanos entre tablas Silver), `temporal_continuity` (sin duplicados exactos de MMSI/tiempo ni deltas negativos) y `spatial_continuity` (velocidades calculadas no mayores a 60 nudos).
*   **Contrato:** Se ejecutan **17 tests dbt** sobre el esquema. Cero violaciones registradas.

### 2.3. QG3: Consistencia Cross-Layer y Freshness (Post-Gold)
Aplica 3 reglas antes de exponer los datos a la API o a modelos de ML.
*   **Reglas:** `gold_completeness` (sin nulos en métricas clave), `cross_layer_consistency` (la suma de distancias en Gold debe coincidir con Silver con un margen del 1%) y `freshness_check` (Gold no debe estar más de 24h detrás de Silver).
*   **Contrato:** Se ejecutan **35 tests dbt** sobre los Data Marts. Cero violaciones registradas.

## 3. El Sistema de Cuarentena (No-Silent Drops)

El antipatrón más peligroso en ingeniería de datos es la **eliminación silenciosa** (dropear registros que no cumplen reglas sin dejar rastro). En esta plataforma, los datos nunca se borran: se aíslan en la tabla `quarantine.quarantine_records`.

*   **Payload Inmutable:** El registro original completo se guarda en formato `JSONB`.
*   **Motivo y Regla:** Se documenta qué regla falló (ej. `valid_speed`) y un texto legible explicando el fallo.
*   **Auditoría Estadística:** En la Fase 5 se implementó una auditoría con **Chi-cuadrado (χ²)** y **Índice de Gini** sobre la cuarentena. Esto permite detectar si una fuente de datos tiene un sesgo sistemático (ej. si el 90% de los rechazos son del mismo tipo de barco).

## 4. Los Tests dbt como Contratos de Datos

dbt no solo transforma datos; aplica restricciones de esquema que actúan como contratos inmutables entre capas.

*   **Tests Genéricos:** `not_null`, `unique`, `relationships` (integridad referencial entre dimensiones y hechos) y `accepted_values` (ej. severidad de anomalía solo puede ser `high`, `medium`, `low`).
*   **Materialización:** El paso de vistas (Silver) a tablas físicas (Gold) implica que, si un test de dbt falla, el orquestador de Airflow detiene el pipeline antes de que el dato corrupto llegue a los dashboards o a la API.

## 5. Gobernanza de la Documentación Técnica

La gobernanza no aplica solo a los datos; aplica al código y a las decisiones. Cada componente implementado sigue el esquema:

> **Problema → Alternativas → Decisión → Justificación → Consecuencias → Mejoras Futuras**

Esto permite que cualquier ingeniero que se una al proyecto entienda el "por qué" detrás de una elección técnica (ej. *¿Por qué se usó Polars y no Pandas?* o *¿Por qué el Filtro de Kalman se aplicó en Silver y no en Gold?*).

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
