<div align="center">

# Data Intelligence Platform

### Una infraestructura abierta de conocimiento para el ciclo de vida completo del dato.

**De los `datos` a la `decisión`, sin cajas negras.**

[![Arquitectura](https://img.shields.io/badge/arquitectura-Medallion-1f7a8c?style=flat-square)](#-arquitectura-de-referencia)
[![Estrategia](https://img.shields.io/badge/estrategia-Local--First%20%2B%20Cloud--Ready-0f2942?style=flat-square)](#-arquitectura-de-referencia)
[![Entorno](https://img.shields.io/badge/entorno-Fedora%20Linux-1f7a8c?style=flat-square)](#-guía-de-inicio-rápido)
[![Stack](https://img.shields.io/badge/stack-Python%20%C2%B7%20Docker%20%C2%B7%20Airflow%20%C2%B7%20dbt%20%C2%B7%20PostgreSQL-0f2942?style=flat-square)](#-stack-tecnológico)
[![Estado](https://img.shields.io/badge/estado-Fase%205%20%C2%B7%20Rigor%20Matem%C3%A1tico%20completado-2f855a?style=flat-square)](#-estado-de-avance)
[![Seguridad](https://img.shields.io/badge/seguridad-RBAC%20%C2%B7%20Least%20Privilege-c53030?style=flat-square)](#-trayectoria-de-seguridad)
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

### Estrategia de arquitectura

La arquitectura sigue el **patrón Medallion** porque resuelve tres problemas fundamentales de la ingeniería de datos moderna:

1. **Separación de responsabilidades.** Cada capa (Bronze, Silver, Gold) tiene un propósito único y bien definido. Bronze preserva la fidelidad al origen, Silver normaliza y enriquece, Gold modela para consumo. Ninguna capa se contamina con las preocupaciones de las otras.

2. **Reprocesamiento sin pérdida.** Como Bronze preserva los datos crudos sin modificación, cualquier problema detectado en Silver o Gold puede resolverse reejecutando las transformaciones sin volver a descargar la fuente original.

3. **Auditoría y trazabilidad.** Cada fila de cada capa puede rastrearse hasta la observación original en Bronze mediante el `ingestion_run_id` y el `ingestion_row_id`, permitiendo responder "¿de dónde vino este número?" en cualquier momento.

Los principios de diseño que guían la implementación son cinco:

| Principio | Significado concreto |
|---|---|
| **Inmutabilidad** | Los datos en Landing y Bronze nunca se modifican, solo se agregan. Los cambios ocurren en capas superiores. |
| **Idempotencia** | Reejecutar un pipeline con el mismo `ingestion_run_id` actualiza registros en lugar de duplicarlos. |
| **Trazabilidad** | Cada registro tiene identificadores que permiten rastrear su origen, transformaciones y destino. |
| **Cuarentena** | Los datos inválidos no se eliminan en silencio: se preservan con causa y contexto. |
| **Assume Breach** | La seguridad se diseña asumiendo que algún componente será comprometido; el daño debe ser limitado. |

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

**Apache Airflow 2.10.2** coordina las dependencias, ejecuciones, reintentos y periodicidad de todo el flujo mediante DAGs definidos con la TaskFlow API. **dbt 1.12** gestiona las transformaciones analíticas entre capas, con 17 tests declarativos en Silver y 35 en Gold. **PostgreSQL 16** materializa el modelo dimensional en seis esquemas (`bronze`, `silver`, `gold`, `metadata`, `quarantine`, `public`). **MinIO** emula S3 durante el desarrollo local, garantizando que la migración a cloud sea un cambio de endpoint, no un rediseño.

### Principios Rectores

| Principio | Significado concreto |
|---|---|
| **Reproducibilidad** | Cualquier persona puede levantar el proyecto completo con instrucciones documentadas. Nada depende de configuraciones no versionadas. |
| **Trazabilidad** | Cada registro tiene un `ingestion_run_id` que permite rastrear su origen, transformaciones y destino. |
| **Cuarentena de datos inválidos** | Los registros que fallan un Quality Gate no se eliminan en silencio: se preservan con causa y regla violada. |
| **Observabilidad** | Freshness, conteos, nulos, duplicados, schema drift e integridad referencial se monitorean activamente. |
| **Local-First + Cloud-Where-Useful** | El desarrollo y la experimentación ocurren localmente; la nube se incorpora donde aporta valor real. |
| **Desacoplamiento del dominio** | Los componentes no asumen el caso marítimo; cualquier dominio puede integrarse sin destruir lo existente. |
| **Assume Breach** | La seguridad se diseña asumiendo que algún componente será comprometido; el daño debe ser limitado. |
| **Least Privilege** | Cada componente tiene solo los permisos que necesita para su función, nada más. |

---

## 📊 Estado de Avance

### ✅ Fase 1 — Bootstrap e Infraestructura

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

**🔒 Postura de seguridad de la Fase 1:**

- **Aislamiento de secretos.** Todas las credenciales viven en `.env`, que está estrictamente excluido de Git mediante `.gitignore` (verificado con `git check-ignore`). El archivo `.env.example` es la plantilla pública: define qué variables existen sin exponer sus valores.
- **Aislamiento de red.** Todos los contenedores viven en una red bridge privada (`docker_default`). Los servicios no son accesibles desde fuera del host salvo por los puertos explícitamente publicados (8080, 9000, 9001, 5432, 5433).
- **Contenedores sin privilegios.** Cada imagen se construye evitando correr como root en runtime; PostgreSQL, MinIO y Airflow corren como usuarios no privilegiados dentro de sus contenedores.
- **Health checks.** Cada servicio tiene health checks configurados que permiten al orquestador detectar fallos y reiniciar contenedores si es necesario.

**Aprendizajes técnicos del bootstrap:**
- Compatibilidad de Polars con CPUs sin AVX2 (`polars-lts-cpu`).
- Migración a espejo comunitario `coollabsio/minio` tras remoción de imágenes oficiales.
- Alineación del entrypoint de Airflow y fijación de providers para evitar Airflow 3.x.
- Resolución DNS del daemon Docker en Fedora (`/etc/docker/daemon.json`).
- Conflictos de puerto entre servicios del sistema y contenedores (PostgreSQL 5432).

### ✅ Fase 2 — Ingestión, Bronze y Quality Gate 1

Primer pipeline end-to-end funcionando: extracción desde fuente sintética (o NOAA real), preservación inmutable en Data Lake y MinIO, estructuración en Bronze con auditoría completa, y validación estructural con aislamiento de registros inválidos en cuarentena.

| Componente | Estado | Evidencia |
|---|---|---|
| **Extractor de AIS** (`ingestion/maritime/noaa_ais.py`) | ✅ | Dataset sintético o NOAA · checksum SHA-256 · Parquet con Zstd |
| **Preservación inmutable** | ✅ | `data/raw/maritime/year=/month=/day=/` + copia en MinIO |
| **Escritor de Bronze** (`src/storage/bronze_writer.py`) | ✅ | 200 filas insertadas con auditoría completa |
| **Quality Gate 1** (`src/validation/quality_gate_1.py`) | ✅ | 6 reglas aplicadas · 170 validadas · 30 a cuarentena |
| **Tabla `metadata.ingestion_runs`** | ✅ | Corrida registrada con estado `bronze_loaded` |
| **Tabla `quarantine.quarantine_records`** | ✅ | Payload JSONB completo por cada rechazo |
| **DAG `dag_01_discovery_ingestion`** | ✅ | 5 tareas en TaskFlow API · retries=2 |

**Métricas de la corrida de verificación:**

| Métrica | Valor |
|---|---|
| Registros procesados | 200 |
| Registros validados | 170 (85%) |
| Registros en cuarentena | 30 (15%) |
| Tamaño del Parquet | 10,497 bytes |
| Distribución de violaciones | `valid_mmsi_format` (10) · `valid_speed` (8) · `valid_mmsi_present` (5) · `valid_longitude` (4) · `valid_timestamp` (4) · `valid_latitude` (4) |

**🔒 Postura de seguridad de la Fase 2:**

- **Prevención de SQL Injection.** Todo el código Python que interactúa con PostgreSQL usa **parámetros vinculados** mediante `text()` de SQLAlchemy con diccionarios. Nunca se concatena SQL con strings. Esta es la defensa más efectiva contra el ataque más común a bases de datos.
- **Auditoría de ingestión.** Cada corrida registra en `metadata.ingestion_runs` el checksum SHA-256 del archivo, su tamaño, y su timestamp. Esto permite detectar si un archivo fue modificado después de su preservación.
- **Aislamiento de payload inválido.** Los registros rechazados no se borran: se preservan con causa en `quarantine.quarantine_records`. La auditoría estadística de esta tabla (Fase 5) permite detectar patrones de sesgo.

### ✅ Fase 3 — Capa Silver, Transformaciones dbt y Quality Gate 2

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

**Métricas reales de la corrida:**

| Métrica | Valor |
|---|---|
| Modelos Silver creados | 3 vistas en esquema `silver` |
| Tests dbt pasados | 17 / 17 |
| Violaciones detectadas por QG2 | 0 (referential + temporal + spatial) |
| Velocidad calculada vs reportada | Delta < 0.05 nudos |
| Distancias entre posiciones | 3.6 – 14.7 km (plausibles) |

**🔒 Postura de seguridad de la Fase 3:**

- **Montaje de perfiles en solo lectura.** El directorio `~/.dbt` del host se monta en el contenedor con `:ro` (read-only). El contenedor puede leer los perfiles de conexión pero no modificarlos. Esto previene que un contenedor comprometido altere la configuración del host.
- **Aislamiento de dependencias.** dbt vive en un virtualenv independiente (`/opt/dbt-venv`) dentro del contenedor de Airflow. Esto evita conflictos de dependencias entre dbt y Airflow, y aísla cualquier vulnerabilidad de dbt del entorno de Airflow.
- **Segmentación de responsabilidades.** El contenedor de Airflow importa módulos de `src/` pero no accede a las credenciales de producción. Los secretos se inyectan vía variables de entorno en runtime.
- **Tests declarativos como barrera.** Los 17 tests de dbt no solo validan calidad de datos: también actúan como contrato implícito entre capas. Si un modelo de Silver dejara de cumplir sus propiedades esperadas, los tests fallarían antes de que el problema llegara a Gold.

### ✅ Fase 4 — Capa Gold, Data Marts y Endurecimiento RBAC

Construcción de la capa analítica final: siete Data Marts que responden preguntas de negocio, motor de Quality Gate 3 con validación cross-layer, y aplicación del principio de **Least Privilege** en PostgreSQL con cuatro usuarios especializados.

| Componente | Estado | Evidencia |
|---|---|---|
| **Modelo `fact_vessel_voyage`** | ✅ | 10 viajes agregados con distancia, duración, velocidad |
| **Modelo `dim_port`** | ✅ | 15 puertos con bounding boxes de ±0.3° |
| **Modelo `agg_port_operations`** | ✅ | 7 filas · 5 puertos con actividad |
| **Modelo `agg_port_congestion`** | ✅ | Índice horario con niveles low/moderate/high/critical |
| **Modelo `vessel_intelligence`** | ✅ | 10 perfiles operativos por embarcación |
| **Modelo `route_intelligence`** | ✅ | Análisis origen-destino con frecuencia |
| **Modelo `anomaly_mart`** | ✅ | Consolidación de anomalías (0 filas, coherente) |
| **Tests dbt Gold** | ✅ | `PASS=35` `ERROR=0` `WARN=0` |
| **Quality Gate 3** | ✅ | 3 reglas · 0 violaciones |
| **RBAC en PostgreSQL** | ✅ | 4 usuarios con permisos mínimos |
| **DAG `dag_03_gold_transformation`** | ✅ | 5 tareas · TaskFlow API + BashOperator |

**Los cuatro usuarios RBAC:**

| Usuario | Función | Permisos |
|---|---|---|
| `pipeline_user` | Scripts de ingestión | INSERT/UPDATE/SELECT en Bronze, Metadata, Quarantine; SELECT en Silver y Gold |
| `dbt_user` | Transformaciones dbt | SELECT en Bronze; ALL en Silver y Gold |
| `api_user` | API REST (futura) | SELECT únicamente sobre Gold |
| `analyst_user` | Análisis ad-hoc | SELECT únicamente sobre Gold |

**Verificación empírica del RBAC:**

```bash
# api_user PUEDE leer Gold
$ docker exec dip-project-postgres psql -U api_user -d maritime -c "SELECT COUNT(*) FROM gold.fact_vessel_voyage;"
 count
-------
    10

# api_user NO PUEDE leer Silver
$ docker exec dip-project-postgres psql -U api_user -d maritime -c "SELECT COUNT(*) FROM silver.int_vessel_tracks;"
ERROR:  permission denied for schema silver
```

**🔒 Postura de seguridad de la Fase 4:**

- **RBAC en PostgreSQL.** Se eliminó el uso del usuario único omnipotente. Cuatro usuarios especializados reemplazan al anterior `maritime_user`: `pipeline_user`, `dbt_user`, `api_user`, `analyst_user`. Cada uno tiene solo los permisos que necesita.
- **Default privileges.** El script `scripts/security/init_rbac_roles.sql` configura `ALTER DEFAULT PRIVILEGES` para que los objetos futuros creados por dbt hereden automáticamente los permisos correctos. No hay que reejecutar el script cada vez que se añade una tabla.
- **Aislamiento por función.** El usuario de la API no puede tocar Bronze, Silver ni Metadata. El usuario de dbt no puede escribir en Bronze. El usuario del pipeline no puede hacer DROP. Cada compromiso queda limitado a un subconjunto mínimo de la base de datos.
- **Trazabilidad de operaciones.** Como cada función usa un usuario distinto, los logs de PostgreSQL registran quién hizo qué. Es trivial distinguir consultas de la API, transformaciones de dbt, y análisis ad-hoc.

**Retos técnicos resueltos:**
- Corridas mezcladas en Bronze por `random.Random(42)` con MMSIs reutilizados → limpieza total y regeneración.
- Puertos vacíos por bounding boxes demasiado pequeños → ampliación a ±0.3° y distribución fija de barcos.

### ✅ Fase 5 — Rigor Matemático, Estadístico y Bayesiano

Refuerzo científico del pipeline: cuatro módulos que elevan el rigor matemático y preparan la infraestructura para Machine Learning.

| Módulo | Estado | Descripción |
|---|---|---|
| **`quarantine_audit.py`** | ✅ | Auditoría estadística de sesgo (Chi², Gini, distribución temporal y geográfica) |
| **`temporal_resampling.py`** | ✅ | Resampling a malla regular de 15 min con interpolación lineal |
| **`kalman_filter.py`** | ✅ | Filtro de Kalman 4D para suavizado de trayectorias GPS |
| **`feature_prep.py`** | ✅ | Pipeline de ML con split temporal y estandarización sin leakage |

**Resultados de la ejecución:**

| Módulo | Resultado |
|---|---|
| **Auditoría** | Chi²=5.63 (p=0.344, uniforme) · Gini=0.152 · 29 celdas geográficas · 0 alertas de sesgo |
| **Resampling** | 307 filas producidas desde 170 · 96.7% interpolado · 0 tracks con gaps > 3h |
| **Kalman** | RMSE 0.06 mm (dataset sintético sin ruido) · 10 tracks procesados |
| **Feature prep** | Split 7/1/2 · scaler guardado solo del train |

**🔒 Postura de seguridad de la Fase 5:**

- **Detección estadística de sesgo.** El módulo `quarantine_audit.py` analiza sistemáticamente si el QG1 rechaza datos de forma sesgada. Un sesgo no detectado puede producir modelos de ML discriminatorios. La auditoría con Chi² y Gini garantiza que el pipeline no introduce sesgos silenciosos.
- **Prevención de data leakage.** El split temporal estricto y la estandarización calculada solo sobre el train previenen que los modelos de ML "vean el futuro" durante el entrenamiento. Sin esta disciplina, las métricas de validación serían engañosamente altas.
- **Calidad del dato antes que la complejidad del modelo.** La filosofía de la fase es clara: no se entrena un modelo sin antes haber validado que los datos no tienen sesgo, no tienen ruido excesivo, y están preparados para ML correctamente.

---

## 🗺️ Hoja de Ruta

### ✅ Completado — Fase 1 (Bootstrap e Infraestructura)

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

### ✅ Completado — Fase 4 (Capa Gold, Data Marts y RBAC)

- [x] Modelo `fact_vessel_voyage` — viajes agregados a partir de tracks.
- [x] Modelo `dim_port` — dimensión de 15 puertos con bounding boxes.
- [x] Modelo `agg_port_operations` — métricas operativas por puerto y día.
- [x] Modelo `agg_port_congestion` — índice horario de congestión.
- [x] Modelo `vessel_intelligence` — perfil consolidado por embarcación.
- [x] Modelo `route_intelligence` — análisis de rutas origen-destino.
- [x] Modelo `anomaly_mart` — consolidación de anomalías detectadas.
- [x] Quality Gate 3 con 3 reglas (incluyendo validación cross-layer) · 0 violaciones.
- [x] RBAC en PostgreSQL con 4 usuarios especializados (Least Privilege).
- [x] DAG `dag_03_gold_transformation` con 5 tareas.

### ✅ Completado — Fase 5 (Rigor Matemático y Preparación de ML)

- [x] Auditoría estadística de sesgo en Cuarentena (`quarantine_audit.py`).
- [x] Test de Chi-cuadrado de uniformidad para distribución por regla.
- [x] Índice de Gini para concentración de rechazos por MMSI.
- [x] Resampling temporal a malla regular de 15 min con interpolación lineal.
- [x] Filtro de Kalman 4D para suavizado de trayectorias GPS.
- [x] Manejo natural de gaps temporales durante la pérdida de señal.
- [x] Pipeline de feature prep con split temporal y estandarización sin leakage.
- [x] Limpieza de outliers con rango intercuartílico (IQR).
- [x] Explicación matemática documentada de las ecuaciones de Kalman.

### 🚧 Próximos hitos — Fase 6 (API REST con FastAPI)

- [ ] Endpoints sobre Gold: `/health`, `/ports`, `/ports/{id}`, `/ports/{id}/congestion`, `/vessels/{id}`, `/vessels/{id}/voyages`, `/routes`, `/anomalies`.
- [ ] Conexión con PostgreSQL usando `api_user` (RBAC ya aplicado).
- [ ] Schemas Pydantic para validación de inputs y outputs.
- [ ] Routers separados por dominio (ports, vessels, routes, anomalies).
- [ ] Documentación automática con OpenAPI/Swagger.
- [ ] Tests con pytest y httpx.
- [ ] Colección Postman para pruebas manuales.
- [ ] Healthcheck para monitoreo.
- [ ] HTTPS y JWT con expiración corta.
- [ ] Rate limiting por IP.

### 🔮 Fases posteriores

- [ ] **Fase 7 — Machine Learning Avanzado:** entrenamiento de modelos de predicción de ETA, forecasting de congestión, y detección de anomalías con Isolation Forest y DBSCAN.
- [ ] **Fase 8 — Intelligence con LLMs:** generación de briefings operacionales con Gemini, con trazabilidad completa de métricas fuente.
- [ ] **Fase 9 — CI/CD:** pipelines con GitHub Actions ejecutando lint, tests, dbt compile, dbt tests, DAG tests, Docker build y Postman.
- [ ] **Fase 10 — Infraestructura Cloud (AWS):** S3, IAM, Lambda, CloudWatch, Secrets Manager, VPC privada, KMS.
- [ ] **Fase 11 — Infraestructura como Código (Terraform):** aprovisionamiento reproducible de todos los recursos cloud.
- [ ] **Fase 12 — Migración a Snowflake:** plataforma analítica cloud con comparación de arquitecturas (Airflow+dbt, Streams+Tasks, Dynamic Tables).

**La arquitectura está preparada para incorporar nuevos dominios sin rediseño**: datos meteorológicos, financieros, urbanos, ambientales, científicos, gubernamentales, deportivos, industriales, o cualquier fuente pública o privada que aporte valor a la comunidad. El caso marítimo es la primera prueba, no la frontera conceptual.

---

## 🔒 Trayectoria de Seguridad

La seguridad en este proyecto no es un apartado estático ni una fase específica: es una **trayectoria de madurez transversal** que evoluciona con cada fase. Este apartado resume las medidas de seguridad aplicadas hasta la fecha y las planificadas para las fases siguientes.

### Seguridad aplicada por fase

| Fase | Medida de seguridad |
|---|---|
| **1. Bootstrap** | `.env` aislado y en `.gitignore` · Aislamiento de red Docker · Contenedores sin privilegios · Health checks |
| **2. Ingestión + Bronze** | Parámetros vinculados en SQL (anti-injection) · Checksums SHA-256 para integridad · Cuarentena de datos inválidos |
| **3. Silver + dbt** | Montaje de perfiles dbt en solo lectura (`:ro`) · Venv aislado para dbt en Airflow · Tests declarativos como contrato entre capas |
| **4. Gold + RBAC** | RBAC con 4 usuarios especializados · Default privileges para objetos futuros · Aislamiento por función · Trazabilidad por usuario |
| **5. Rigor Matemático** | Detección estadística de sesgo en cuarentena · Prevención de data leakage en ML · Split temporal estricto |

### Seguridad planificada por fase

| Fase | Medida de seguridad planificada |
|---|---|
| **6. API REST** | HTTPS con TLS 1.3 · JWT con expiración corta · Rate limiting por IP · CORS restrictivo · Validación con Pydantic |
| **7. ML Avanzado** | Modelos sin data leakage verificado · Explicabilidad con SHAP · Monitoreo de drift |
| **8. Intelligence (LLMs)** | Prompts sin datos sensibles · Validación de outputs generados · Auditoría de llamadas a APIs externas |
| **9. CI/CD** | GitHub Secrets para credenciales · Escaneo de dependencias (Dependabot) · Análisis de código estático (SAST) |
| **10. Cloud (AWS)** | AWS Secrets Manager · VPC privada con subnets · Security Groups restrictivos · KMS para cifrado en reposo · CloudWatch para logs |
| **11. Terraform** | State cifrado en S3 · Backend remoto con locking · Revisión de plan antes de apply |
| **12. Snowflake** | RBAC de Snowflake · Row-level security · Data masking para PII · Auditoría con ACCESS_HISTORY |

### El principio que guía todo

> **La seguridad no es un producto que se instala, es una propiedad que emerge del diseño.**
>
> Ningún firewall, ningún WAF, ninguna herramienta mágica hace el sistema seguro. Lo que lo hace seguro es pensar cada componente asumiendo que algo puede salir mal, y construir en consecuencia. La seguridad es un hábito, no un evento.

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

### Quality Gate 3 — Calidad analítica (post-Gold) · ✅ implementado

Aplica 3 reglas sobre Gold:
- **`gold_completeness`** — verifica que `fact_vessel_voyage` no tenga nulos ni ceros inconsistentes.
- **`cross_layer_consistency`** — compara la suma de distancias en Gold contra Silver, con tolerancia del 1%.
- **`freshness_check`** — verifica que Gold no esté más de 24 horas detrás de Silver.

### Gobernanza de datos

| Aspecto | Implementación |
|---|---|
| **Linaje** | Cada fila rastreable hasta el archivo original vía `ingestion_run_id` y `ingestion_row_id` |
| **Metadatos** | Registrados en `metadata.ingestion_runs` (checksum, tamaño, timestamps, source) |
| **Cuarentena** | Registros inválidos preservados con payload JSONB completo y reglas violadas |
| **Contratos de datos** | Tests dbt como contrato implícito entre capas (17 en Silver, 35 en Gold) |
| **Auditoría estadística** | Análisis de sesgo con Chi², Gini, distribución temporal y geográfica |
| **Documentación de decisiones** | Cada decisión técnica sigue el esquema: problema → alternativas → decisión → justificación → consecuencias → mejoras futuras |

### Automatización de calidad

- **Ruff** — linter y formateador ultrarrápido, configurado en `pyproject.toml`.
- **mypy** — verificación estática de tipos, con `disallow_untyped_defs = true`.
- **pytest** — framework de testing con marcadores por tipo (`unit`, `integration`, `data_quality`, `slow`).
- **pre-commit** — hooks automáticos que ejecutan todas las verificaciones antes de cada commit.
- **dbt tests** — 17 tests en Silver + 35 tests en Gold.

Con pre-commit y los Quality Gates activos, es imposible que un dato inválido llegue a Gold, y es imposible commitear código que no pase Ruff, mypy y los tests.

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
│   │   ├── noaa_ais.py               # Extractor principal (sintético o NOAA real)
│   │   └── __init__.py
│   ├── ports/                        # World Port Index
│   └── weather/                      # Fuentes meteorológicas
│
├── src/                              # Código fuente modular
│   ├── config.py                     # Configuración tipada con Pydantic
│   ├── logging_config.py             # Logging estructurado
│   ├── storage/
│   │   ├── db.py                     # Engine de SQLAlchemy cacheado
│   │   ├── s3_lake.py                # Cliente S3/MinIO cacheado
│   │   └── bronze_writer.py          # Escritor a Bronze con auditoría
│   ├── validation/
│   │   ├── quality_gate_1.py         # 6 reglas estructurales post-Bronze
│   │   ├── quality_gate_2.py         # 3 reglas analíticas post-Silver
│   │   ├── quality_gate_3.py         # 3 reglas cross-layer post-Gold
│   │   └── quarantine_audit.py       # Auditoría estadística de sesgo (Fase 5)
│   ├── transformations/              # Nuevos módulos de Fase 5
│   │   ├── temporal_resampling.py    # Resampling a malla regular
│   │   └── kalman_filter.py          # Filtro de Kalman 4D
│   ├── ml/                           # Machine Learning
│   │   ├── feature_prep.py           # Pipeline de features sin leakage
│   │   ├── train.py                  # (Fase 7)
│   │   └── evaluate.py               # (Fase 7)
│   ├── geospatial/                   # Geofencing y H3
│   ├── tracking/                     # Reconstrucción de trayectorias
│   └── features/                     # Ingeniería de variables
│
├── airflow/                          # Orquestador
│   ├── dags/
│   │   ├── dag_01_discovery_ingestion.py
│   │   ├── dag_02_silver_transformation.py
│   │   └── dag_03_gold_transformation.py
│   ├── plugins/
│   ├── Dockerfile                    # Imagen con dbt en venv aislado
│   └── requirements.txt
│
├── dbt/maritime/                     # Transformaciones analíticas
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── macros/
│   │   └── generate_schema_name.sql
│   ├── models/
│   │   ├── staging/                  # Silver: normalización
│   │   │   ├── _sources.yml
│   │   │   ├── stg_ais_position.sql
│   │   │   └── stg_ais_position.yml
│   │   ├── intermediate/             # Silver: enriquecimiento
│   │   │   ├── int_vessel_position_deltas.sql
│   │   │   ├── int_vessel_tracks.sql
│   │   │   └── schema.yml
│   │   └── marts/                    # Gold: Data Marts
│   │       ├── core/
│   │       │   ├── fact_vessel_voyage.sql
│   │       │   └── schema.yml
│   │       ├── port_operations/
│   │       │   ├── dim_port.sql
│   │       │   ├── agg_port_operations.sql
│   │       │   └── schema.yml
│   │       ├── port_congestion/
│   │       │   ├── agg_port_congestion.sql
│   │       │   └── schema.yml
│   │       ├── vessel_intelligence/
│   │       │   ├── vessel_intelligence.sql
│   │       │   └── schema.yml
│   │       ├── route_intelligence/
│   │       │   ├── route_intelligence.sql
│   │       │   └── schema.yml
│   │       └── anomaly/
│   │           ├── anomaly_mart.sql
│   │           └── schema.yml
│   ├── snapshots/
│   ├── tests/
│   └── seeds/
│
├── api/                              # API REST con FastAPI (Fase 6)
│   └── app/
│       ├── main.py
│       ├── routers/
│       └── schemas/
│
├── intelligence/                     # Capa de inteligencia generativa (Fase 8)
│   ├── prompts/
│   ├── schemas/
│   └── gemini/
│
├── docker/                           # Stack de desarrollo local
│   ├── docker-compose.yml
│   ├── postgres/init/
│   │   ├── 01_create_databases.sql
│   │   └── 02_bronze_quarantine_metadata.sql
│   └── minio/
│
├── scripts/                          # Automatización
│   ├── bootstrap.sh
│   ├── check_environment.sh
│   ├── seed_data.sh
│   └── security/                     # Scripts de RBAC (Fase 4)
│       ├── init_rbac_roles.sql
│       └── apply_rbac.sh
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
- dbt responde con su versión.

### Paso 5 — Verificar la conexión de dbt

```bash
cd dbt/maritime
export DBT_PROFILES_DIR=~/.dbt
set -a; source ../../.env; set +a

dbt debug
```

Salida esperada: **`All checks passed!`**

### Paso 6 — Aplicar el RBAC en PostgreSQL

```bash
cd ~/Projects/data-intelligence-platform
./scripts/security/apply_rbac.sh
```

Esto crea los cuatro usuarios especializados (`pipeline_user`, `dbt_user`, `api_user`, `analyst_user`) con sus permisos mínimos.

### Paso 7 — Ejecutar el pipeline completo (Fases 2, 3 y 4)

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

# --- FASE 4: Gold con dbt + QG3 ---
dbt run --select tag:gold --no-version-check
dbt test --select tag:gold --no-version-check

cd ~/Projects/data-intelligence-platform
python -c "from src.validation.quality_gate_2 import run_quality_gate_2; import json; print(json.dumps(run_quality_gate_2(), indent=2, default=str))"
python -c "from src.validation.quality_gate_3 import run_quality_gate_3; import json; print(json.dumps(run_quality_gate_3(), indent=2, default=str))"
```

**Opción B — Disparar desde Airflow (valida la orquestación completa):**

```bash
# DAG 01 (Bronze)
docker exec dip-airflow-webserver airflow dags unpause dag_01_discovery_ingestion
docker exec dip-airflow-webserver airflow dags trigger dag_01_discovery_ingestion

# DAG 02 (Silver) — después de que DAG 01 termine
docker exec dip-airflow-webserver airflow dags unpause dag_02_silver_transformation
docker exec dip-airflow-webserver airflow dags trigger dag_02_silver_transformation

# DAG 03 (Gold) — después de que DAG 02 termine
docker exec dip-airflow-webserver airflow dags unpause dag_03_gold_transformation
docker exec dip-airflow-webserver airflow dags trigger dag_03_gold_transformation

# Estado de los runs
for d in dag_01_discovery_ingestion dag_02_silver_transformation dag_03_gold_transformation; do
    docker exec dip-airflow-webserver airflow dags list-runs -d $d 2>/dev/null | head -3
done
```

Interfaz web en `http://localhost:8080` (usuario `admin` / contraseña `admin`) → **DAGs → Graph**.

### Paso 8 — Ejecutar los módulos de la Fase 5 (Rigor Matemático)

```bash
cd ~/Projects/data-intelligence-platform
source .venv/bin/activate
set -a; source .env; set +a

# 1. Auditoría estadística de sesgo
python -c "from src.validation.quarantine_audit import run_quarantine_audit; import json; print(json.dumps(run_quarantine_audit(), indent=2, default=str))"

# 2. Resampling temporal
python -c "from src.transformations.temporal_resampling import resample_from_silver, summary; r = resample_from_silver(interval_minutes=15); print(summary(r))"

# 3. Filtro de Kalman
python -c "from src.transformations.kalman_filter import smooth_from_silver, summary; s = smooth_from_silver(); print(summary(s))"

# 4. Preparación de features para ML
python -c "from src.ml.feature_prep import prepare_vessel_features; r = prepare_vessel_features(); print({k: v for k, v in r.items() if k not in ('train', 'validation', 'test')})"
```

### Paso 9 — Verificar los resultados en PostgreSQL

```bash
export RUN_ID=$(docker exec dip-project-postgres psql -U maritime_user -d maritime -t -A -c "SELECT ingestion_run_id FROM metadata.ingestion_runs ORDER BY created_at DESC LIMIT 1")

# --- Bronze y Cuarentena ---
docker exec dip-project-postgres psql -U maritime_user -d maritime -c "
    SELECT quality_status, COUNT(*) FROM bronze.bronze_ais_position
    WHERE ingestion_run_id = '$RUN_ID' GROUP BY quality_status;"

# --- Silver ---
docker exec dip-project-postgres psql -U maritime_user -d maritime -c "
    SELECT table_schema, table_name FROM information_schema.tables
    WHERE table_schema IN ('silver', 'gold') ORDER BY 1, 2;"

# --- Gold ---
for t in fact_vessel_voyage dim_port agg_port_operations agg_port_congestion vessel_intelligence route_intelligence anomaly_mart; do
    docker exec dip-project-postgres psql -U maritime_user -d maritime -t -c "SELECT '$t', COUNT(*) FROM gold.$t;"
done
```

### Interfaces disponibles tras el arranque

| Servicio | URL | Credenciales | Propósito |
|---|---|---|---|
| **Airflow Webserver** | http://localhost:8080 | `admin` / `admin` | Orquestador de pipelines y logs de ejecución. |
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin` | Navegador del Data Lake (buckets y archivos Parquet). |
| **pgAdmin** | http://localhost:5050 | `admin@example.com` / `admin` | Interfaz gráfica para explorar PostgreSQL. |
| **Portainer** | https://localhost:9443 | *Crear al primer ingreso* | Monitor de contenedores Docker, CPU y RAM. |
| **dbt docs** | http://localhost:8081 | — | Linaje visual y catálogo de modelos dbt. |
| **PostgreSQL (proyecto)** | `localhost:5432` | `maritime_user` / `change_me_dev_only` | Conexión directa (opcional si usas pgAdmin). |
| **PostgreSQL (Airflow)** | `localhost:5433` | `airflow` / `change_me_dev_only` | Conexión directa (opcional). |

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

**Data Intelligence Platform** · Fase 5 · Rigor Matemático y Preparación de ML completados

*Construido con rigor, documentado con honestidad, abierto a quien quiera aprender.*

</div>
