<div align="center">

# 🏛️ Data Intelligence Platform

### Infraestructura abierta para el ciclo de vida completo del dato: desde la ingesta cruda hasta la API de consumo.

**De los datos a la decisión, sin límites en lo que podemos aprender.**

[![Arquitectura](./documentation/02_architecture.md)](./documentation/02_architecture.md)
[![Estado](./documentation/03_status_phases.md)](./documentation/03_status_phases.md)
[![Seguridad](./documentation/04_security_roadmap.md)](./documentation/04_security_roadmap.md)
[![Stack](./documentation/02_architecture.md)](./documentation/02_architecture.md)
[![Licencia](./LICENSE)](./LICENSE)

</div>

---

## 🛠️ El "Por Qué": Pasión por Entender la Maquinaria

Vivimos en una era donde las plataformas de datos modernas suelen venderse como soluciones cerradas. El usuario final inserta datos y recibe métricas, pero la mecánica interna —cómo se valida la calidad, cómo se aíslan las cargas o cómo se previenen errores— a menudo queda oculta.

Este proyecto nace desde la **Escuela de Estadística y Ciencias Actuariales (UCV)** con una convicción muy clara: **la mejor forma de aprender ingeniería de datos es construyéndola desde cero y compartiendo el proceso.**

No es solo un ejercicio académico; es una implementación de nivel producción que, hoy, opera con **datos reales a escala**: el archivo diario oficial de NOAA AIS (**8.1 millones de registros**) y el World Port Index real (**3,804 puertos**), expuestos a través de la API y listos para ML. El ciclo de vida completo es real: `Datos → Información → Análisis → Conocimiento → Inteligencia → Decisión`. Utilizando el tráfico marítimo (AIS) como banco de pruebas, hemos diseñado una arquitectura desacoplada del dominio, pensada para que otros estudiantes e ingenieros puedan estudiarla, reproducirla y expandirla.

Buscamos demostrar que la transparencia técnica y el uso de herramientas open-source (como Airflow, dbt y FastAPI) pueden igualar el rigor de las plataformas empresariales más complejas. Nuestros pilares de diseño son:

*   **Inmutabilidad y Contratos de Datos:** Los datos en Landing y Bronze nunca se alteran. Cada transición entre capas está regida por *Quality Gates* y validaciones declarativas (dbt), con tolerancia estadística calibrada para el ruido real de los GPS marinos.
*   **Trazabilidad Absoluta:** Cada registro cuenta con un `ingestion_run_id` y `ingestion_row_id`, permitiendo auditar el linaje desde el archivo original hasta la API final.
*   **Pipeline Idempotente:** Toda la ingesta es repetible: validación por `source_url` y checksum SHA-256 (ciclo de vida `landed → completed`) garantiza que re-ejecutar un DAG nunca duplique los 8.1M de registros.
*   **Ingeniería para Escala Real:** Archivos diarios de gigabytes se procesan con la **Lazy API de Polars** (`scan_csv` + `sink_parquet`, streaming sin agotar la RAM) y se cargan en PostgreSQL con **COPY masivo** (`SET LOCAL synchronous_commit = OFF`), completando la carga de Bronze en segundos.
*   **Aislamiento de Recursos:** Orquestación local *Local-First* (Docker, MinIO) lista para migrar a Cloud (*Cloud-Where-Useful*).
*   **Seguridad por Diseño (Assume Breach):** Cuatro roles dedicados en base de datos (RBAC) garantizan que la API solo tenga acceso a la capa de consumo (Gold), minimizando el radio de acción ante cualquier fallo.

---

## ⚡ Estado de Avance: 8 Fases Cerradas y Validadas

El pipeline no es teoría. Desde la Fase 8 opera con **datos reales de NOAA (AIS) y del World Port Index**, con un entorno local *end-to-end* validado mediante pruebas automatizadas y Quality Gates calibrados contra el ruido real del sensor GPS marino.

| Fase | Hito Arquitectónico | Validación Técnica |
| :--- | :--- | :--- |
| **1** | 🏗️ **Bootstrap & Docker** | Entorno orquestado (Postgres, Airflow, MinIO, dbt) con aislamiento estricto de redes y secretos. |
| **2** | 🥉 **Ingestión & Bronze** | Extracción AIS (Polars) + checksums SHA-256. **QG1:** validación de tipos, rangos físicos y cuarentena JSONB. |
| **3** | 🥈 **Capa Silver & dbt** | Modelos (Haversine, Tracks). **17 tests dbt** en verde. **QG2** en verde. |
| **4** | 🥇 **Capa Gold & RBAC** | **7 Data Marts** analíticos. **QG3:** Validación *cross-layer*. **RBAC:** 4 usuarios con *Least Privilege*. |
| **5** | 🧠 **Rigor Matemático** | Filtro de Kalman 4D (suavizado GPS), resampling temporal y *feature prep* sin *data leakage*. |
| **6** | 🔌 **API REST (FastAPI)** | Fachada asíncrona con **JWT**, *Rate Limiting*, validación Pydantic y conexión restringida a Gold. |
| **7** | 🤖 **Machine Learning** | **XGBoost (ETA)**, **Causalidad de Granger**, ingesta de puertos NGA y endpoint `/predict/eta`. |
| **8** | 🚀 **Hardening de Producción** | **8.1M registros NOAA reales**, idempotencia SHA-256 (`landed → completed`), **COPY masivo + Lazy API** (Bronze en segundos), **3,804 puertos reales (espejo Hugging Face)**, Silver materializado como `table` con `post-hooks` de índices y **QG2 con threshold de tolerancia del 1%**. |

---

## 📂 Estructura del Repositorio

```text
data-intelligence-platform/
├── README.md                 # Portal principal y guía de navegación
├── documentation/            # Portal modular de conocimiento técnico
│   ├── index.md              # Índice general del portal
│   ├── 01_vision_purpose.md  # Visión, propósito y principios
│   ├── 02_architecture.md    # Arquitectura de referencia y stack
│   ├── 03_status_phases.md   # Radiografía técnica de las fases
│   ├── 04_security_roadmap.md# Seguridad, RBAC y Assume Breach
│   ├── 05_quality_governance.md# Calidad, linaje, QG y tolerancia de ruido
│   ├── 06_quickstart_guide.md# Guía de inicio rápido (Fedora/Docker)
│   └── 07_roadmap.md         # Hoja de ruta (Fases 9 a 12)
├── data/                     # Data Lake Local (Estructura Hive / S3)
│   ├── raw/                  # Capa Landing inmutable
│   ├── bronze/               # Fidelidad estructural
│   ├── silver/               # Normalización y trazas
│   ├── gold/                 # Data Marts dimensionales
│   ├── quarantine/           # Aislamiento de errores (JSONB)
│   └── metadata/             # Metadatos de ejecución + idempotencia
├── ingestion/                # Scripts de extracción de fuentes externas
│   ├── maritime/             # NOAA AIS real (Lazy API + COPY masivo + idempotencia)
│   └── ports/                # World Port Index (espejo CSV Hugging Face)
├── src/                      # Código fuente modular (Core lógico)
│   ├── config.py             # Configuración y Settings (Pydantic)
│   ├── storage/              # Clientes de base de datos y S3 (Boto3)
│   ├── validation/           # Quality Gates 1, 2 y 3
│   ├── transformations/      # Módulos matemáticos (Kalman, Resampling)
│   └── ml/                   # Módulos de Machine Learning (Fase 7)
│       ├── preprocessing.py  # Split temporal y PCA
│       ├── causal_analysis.py# Test de Causalidad de Granger
│       ├── models.py         # XGBoost e Isolation Forest
│       ├── registry.py       # Model Registry (MinIO S3)
│       └── train.py          # Pipeline de entrenamiento
├── airflow/                  # Orquestador y flujos de trabajo
│   ├── dags/                 # Definición de DAGs de Airflow
│   └── Dockerfile            # Imagen personalizada con dbt aislado
├── dbt/maritime/             # Transformaciones analíticas (ELT)
│   ├── models/               # Modelos Staging, Intermediate y Marts
│   ├── macros/               # Macros SQL personalizadas (Haversine)
│   └── dbt_project.yml       # Configuración de dbt Core 1.12
├── api/                      # Capa de consumo y exposición
│   └── app/
│       ├── main.py           # Aplicación principal FastAPI
│       ├── routers/          # Endpoints por dominio (ports, vessels, predict)
│       ├── schemas/          # Modelos de validación de esquemas (Pydantic)
│       └── core/             # Seguridad, JWT y Rate Limiting
├── docker/                   # Contenedores e infraestructura local
│   ├── docker-compose.yml    # Orquestación de servicios base
│   ├── postgres/init/        # Scripts SQL de inicialización, índices y RBAC
│   └── minio/                # Configuración de buckets locales
├── scripts/                  # Automatización y utilidades de entorno
│   └── security/             # Scripts de aplicación de RBAC en Postgres
└── tests/                    # Suite de pruebas automatizadas (Pytest)
```

---

## 📚 Portal de Documentación Modular

Para mantener el código mantenible y una lectura sin sobrecarga cognitiva, la arquitectura y las decisiones están divididas en manuales técnicos dentro de la carpeta `documentation/`:

| Icono | Documento | Propósito |
| :---: | :--- | :--- |
| 🎯 | **[Visión y Principios](./documentation/01_vision_purpose.md)** | Los fundamentos de ingeniería, el caso de uso y el modelo de colaboración. |
| 🏛️ | **[Arquitectura de Referencia](./documentation/02_architecture.md)** | El flujo Medallion, la pila tecnológica y las estrategias de carga masiva. |
| 📊 | **[Estado y Fases](./documentation/03_status_phases.md)** | Radiografía técnica de las 8 fases, incluida la Fase 8 de producción. |
| 🔒 | **[Seguridad y RBAC](./documentation/04_security_roadmap.md)** | Postura de seguridad, trayectoria evolutiva y *Least Privilege*. |
| 🎯 | **[Calidad y Gobernanza](./documentation/05_quality_governance.md)** | Contratos de datos, linaje, la Triple Barrera de Calidad y el *Threshold* del 1%. |
| 🚀 | **[Guía de Inicio Rápido](./documentation/06_quickstart_guide.md)** | El paso a paso en terminal para levantar toda la plataforma en Fedora. |
| 🗺️ | **[Hoja de Ruta (Roadmap)](./documentation/07_roadmap.md)** | Próximos hitos: ML Avanzado, LLMs con Gemini, AWS y Snowflake. |

---

## 🖥️ Panel de Control: Interfaces Gráficas Locales

Una vez desplegado el stack local (`docker compose up -d`), el control y la observabilidad del sistema se materializan en las siguientes interfaces visuales:

| Interfaz | URL Local | Credenciales | Propósito Operativo |
| :--- | :--- | :--- | :--- |
| 🌪️ **Apache Airflow** | [http://localhost:8080](http://localhost:8080) | `admin` / `admin` | Orquestación de DAGs y monitoreo de ejecuciones. |
| ⚡ **FastAPI Swagger** | [http://localhost:8001/docs](http://localhost:8001/docs) | *(JWT Auth)* | Explorador interactivo de la API REST de la capa Gold. |
| 🗄️ **MinIO Console** | [http://localhost:9001](http://localhost:9001) | `minioadmin` / `minioadmin` | Navegador del Data Lake (Buckets S3 y archivos Parquet). |
| 🐘 **pgAdmin** | [http://localhost:5050](http://localhost:5050) | `admin@example.com` / `admin` | Administración e inspección gráfica de PostgreSQL. |
| 🐳 **Portainer** | [https://localhost:9443](https://localhost:9443) | *(Configurar)* | Observabilidad de contenedores Docker (CPU/RAM). |
| 📊 **dbt Docs** | Ejecutar `./scripts/serve_dbt_docs.sh` | *(Automático)* | Catálogo visual y grafo de linaje de las transformaciones. |

---

## 🤝 Contribución y Transferencia de Conocimiento

Este repositorio es un espacio abierto para la ingeniería y la experimentación. El verdadero valor educativo no reside únicamente en el código funcional, sino en la documentación explícita de las decisiones arquitectónicas (bajo el esquema: *problema → alternativas → decisión → justificación → consecuencias*).

Invitamos a estudiantes, docentes e ingenieros a clonar el proyecto, auditar los pipelines, romper cosas, arreglarlas y proponer mejoras. Consulta la **[Guía de Inicio Rápido](./documentation/06_quickstart_guide.md)** para configurar el entorno.

## 📄 Licencia

Distribuido bajo la **Licencia MIT**. Consulta [`LICENSE`](./LICENSE) para más detalles.

---

<div align="center">
<i>Construido con rigor de ingeniería, documentado con honestidad técnica y abierto a quien quiera aprender.</i>
<br>
<b>Data Intelligence Platform · Fase 8 · Producción con Datos Reales · 2026</b>
</div>
