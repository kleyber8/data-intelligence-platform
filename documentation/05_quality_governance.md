# 🎯 Calidad y Gobernanza de Datos

En arquitecturas de datos modernas, la calidad no es un proceso de "revisión al final del pipeline". La calidad y la gobernanza son **contratos de datos** aplicados en cada transición de capa. Un pipeline que mueve datos rápido pero con datos corruptos o no rastreables es un pasivo, no un activo.

## 1. El Linaje Absoluto (Data Lineage)

Cada registro que fluye por la plataforma es auditable hasta su origen físico. Para lograr esto, el pipeline inyecta metadatos de trazabilidad desde la primera línea de código:

*   **`ingestion_run_id` (UUIDv4):** Identifica la corrida completa del pipeline. Permite agrupar todos los registros de una ingesta específica (ej. descarga del 28 de octubre).
*   **`ingestion_row_id` (UUIDv4):** Asignado a cada fila en la capa Bronze. Permite rastrear un registro individual a través de sus transformaciones en Silver y Gold.
*   **`source_file`:** Almacena la ruta del archivo Parquet original en el Data Lake.
*   **`checksum_sha256` + ciclo `landed → completed`:** El run de ingesta registra en `metadata.ingestion_runs` el SHA-256 del archivo de origen y su estado (`landed` al aterrizar el Parquet, `completed` tras el COPY a Bronze). Esto convierte al linaje también en **llave de idempotencia**: una re-ejecución del DAG 01 con el mismo archivo diario devuelve `already_processed` y mantiene el contrato de unicidad del dato (0 duplicados garantizados).

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
*   **Contrato original (datos sintéticos):** Se ejecutan **17 tests dbt** sobre el esquema. Cero violaciones registradas: con un dataset sintético determinístico, la expectativa razonable era perfección.

### 2.2.1. El Nuevo Threshold de Tolerancia del 1% (Datos Reales AIS)

Al migrar a datos reales (archivo diario de NOAA con 8.1 millones de posiciones), el contrato perfeccionista de QG2 se volvió **físicamente imposible de satisfacer al 100%** — y lo correcto es que así sea:

*   **Por qué el ruido real es esperado:** los receptores GPS marinos de clase AIS reportan con precisión y frecuencia variables (transmisores económicos, antenas mal instaladas, saltos entre ciudades satelitales/terrestres, desfases de reloj entre la hora de reporte y la hora de llegada). La reconstrucción de velocidad entre dos pings consecutivos puede producir cálculos físicamente irreales (velocidades aparentes > 60 nudos) **sin que el transponder esté defectuoso ni la fila esté corrupta**: es ruido de medición GPS sobre el mar, no falta de calidad en el dato.
*   **La primera corrida con datos reales:** el archivo diario real generó **2,849 violaciones** catalogadas por el QG2 (dominadas por `spatial_continuity`: velocidades calculadas por encima del límite físico de 60 nudos). Bajo el contrato original (violaciones == 0 → FAIL), el pipeline quedaba bloqueado con el 99.9+% del dataset perfectamente utilizable. Un gate que bloquea el 100% del flujo por el 0.03% del dato es un gate mal calibrado.
*   **El nuevo criterio de evaluación:** el QG2 ya **no bloquea por un solo error**. El gate ahora evalúa el **porcentaje global de violaciones** sobre el total de registros analizados: si la tasa de violación agregada ≤ **1%**, el gate decide `PASS` y las filas marcadas quedan auditadas en cuarentena y visibles en el `anomaly_mart`. Si la tasa supera el 1%, el gate bloquea el pipeline (sí sigue siendo una barrera de contención). El threshold actúa como declaración formal: *"aceptamos hasta 1% de ruido físico irrecuperable en GPS marino por ciclo diario; por encima de eso, el problema es la fuente, no el sensor"*.

> **Decisión de gobernanza:** el threshold del 1% no es una concesión de la calidad — es el reconocimiento de la naturaleza física del dato AIS, un ruido que desde la Fase 5 ya se trataba estadísticamente con el Filtro de Kalman para el suavizado del GPS. La cuarentena y el Linaje Absoluto siguen dando audibilidad a cada fila segregada; el consumo analítico de Gold simplemente deja de bloquearse por un fenómeno conocido y medible.

### 2.3. QG3: Consistencia Cross-Layer y Freshness (Post-Gold)
Aplica 3 reglas antes de exponer los datos a la API o a modelos de ML.
*   **Reglas:** `gold_completeness` (sin nulos en métricas clave), `cross_layer_consistency` (la suma de distancias en Gold debe coincidir con Silver con un margen del 1%) y `freshness_check` (Gold no debe estar más de 24h detrás de Silver).
*   **Contrato:** Se ejecutan **35 tests dbt** sobre los Data Marts. Cero violaciones registradas.

## 3. El Sistema de Cuarentena (No-Silent Drops)

El antipatrón más peligroso en ingeniería de datos es la **eliminación silenciosa** (dropear registros que no cumplen reglas sin dejar rastro). En esta plataforma, los datos nunca se borran: se aíslan en la tabla `quarantine.quarantine_records`.

*   **Payload Inmutable:** El registro original completo se guarda en formato `JSONB`.
*   **Motivo y Regla:** Se documenta qué regla falló (ej. `valid_speed`) y un texto legible explicando el fallo.
*   **Auditoría Estadística:** En la Fase 5 se implementó una auditoría con **Chi-cuadrado (χ²)** y **Índice de Gini** sobre la cuarentena. Esto permite detectar si una fuente de datos tiene un sesgo sistemático (ej. si el 90% de los rechazos son del mismo tipo de barco).
*   **Umbral del 1% bajo el mismo principio:** las violaciones del QG2 toleradas por el threshold no desaparecen: quedan contabilizadas, auditadas y trazables por `ingestion_run_id`. La tolerancia aplica a la **decisión de bloqueo del pipeline**, nunca al principio de *no-silent drops*.

## 4. Los Tests dbt como Contratos de Datos

dbt no solo transforma datos; aplica restricciones de esquema que actúan como contratos inmutables entre capas.

*   **Tests Genéricos:** `not_null`, `unique`, `relationships` (integridad referencial entre dimensiones y hechos) y `accepted_values` (ej. severidad de anomalía solo puede ser `high`, `medium`, `low`).
*   **Materialización:** los modelos Silver se materializan como **tablas físicas (`table`)** con `post-hooks` que recrean los índices de soporte. Esto resolvió los deadlocks de dbt bajo volumen real y, además, implica que si un test de dbt falla, el orquestador de Airflow detiene el pipeline antes de que el dato corrupto llegue a los dashboards o a la API.
*   **Acoplamiento de los gates:** DAG 03 (Gold) espera la finalización del QG2 de DAG 02 (Silver) mediante `ExternalTaskSensor`, garantizando que ningún mart se construya sobre una capa Silver no validada en el mismo ciclo.

## 5. Gobernanza de la Documentación Técnica

La gobernanza no aplica solo a los datos; aplica al código y a las decisiones. Cada componente implementado sigue el esquema:

> **Problema → Alternativas → Decisión → Justificación → Consecuencias → Mejoras Futuras**

Esto permite que cualquier ingeniero que se una al proyecto entienda el "por qué" detrás de una elección técnica (ej. *¿Por qué se usó Polars y no Pandas?*, *¿Por qué el QG2 ahora evalúa un porcentaje global y no violaciones individuales?* o *¿Por qué el Filtro de Kalman se aplicó en Silver y no en Gold?*).

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
