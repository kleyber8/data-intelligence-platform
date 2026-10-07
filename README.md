<div align="center">

# Data Intelligence Platform

### Una infraestructura abierta de conocimiento para el ciclo de vida completo del dato.

**De los `datos` a la `decisión`, sin cajas negras.**

[![Arquitectura](https://img.shields.io/badge/arquitectura-Medallion-1f7a8c?style=flat-square)](#-arquitectura-de-referencia)
[![Estrategia](https://img.shields.io/badge/estrategia-Local--First%20%2B%20Cloud--Ready-0f2942?style=flat-square)](#-arquitectura-de-referencia)
[![Entorno](https://img.shields.io/badge/entorno-Fedora%20Linux-1f7a8c?style=flat-square)](#-guía-de-inicio-rápido)
[![Stack](https://img.shields.io/badge/stack-Python%20%C2%B7%20Docker%20%C2%B7%20Airflow%20%C2%B7%20dbt%20%C2%B7%20PostgreSQL-0f2942?style=flat-square)](#-stack-tecnológico)
[![Estado](https://img.shields.io/badge/estado-Fase%201%20%C2%B7%20Bootstrap%20completado-2f855a?style=flat-square)](#-estado-de-avance)
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

**Aprendizajes técnicos del bootstrap:**
- Compatibilidad de Polars con CPUs sin AVX2 (`polars-lts-cpu`).
- Desaparición de las imágenes oficiales de MinIO (migración a espejo comunitario `coollabsio/minio`).
- Alineación del entrypoint de Airflow (`dip-airflow-init`).
- Conflictos de dependencias pip ↔ Airflow 3.x (fijación de providers).
- Resolución DNS del daemon Docker en Fedora (`/etc/docker/daemon.json`).

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
│   ├── storage/                      # Abstracción de almacenamiento (local, S3)
│   ├── validation/                   # Quality Gates 1, 2 y 3
│   ├── geospatial/                   # Geofencing y H3
│   ├── tracking/                     # Reconstrucción de trayectorias
│   ├── features/                     # Ingeniería de variables para ML
│   └── ml/                           # Entrenamiento y evaluación
│
├── airflow/                          # Orquestador
│   ├── dags/                         # 7 DAGs (Discovery, Bronze, Silver, Gold, ML, Intelligence, Monitoring)
│   ├── plugins/                      # Operadores personalizados
│   ├── Dockerfile                    # Imagen personalizada
│   └── requirements.txt              # Dependencias del contenedor
│
├── dbt/maritime/                     # Transformaciones analíticas
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── models/
│   │   ├── staging/                  # Capa Silver: normalización
│   │   ├── intermediate/             # Capa Silver: enriquecimiento
│   │   └── marts/                    # Capa Gold: Data Marts
│   │       ├── core/
│   │       ├── port_operations/
│   │       ├── port_congestion/
│   │       ├── vessel_intelligence/
│   │       ├── route_intelligence/
│   │       └── anomaly/
│   ├── snapshots/
│   ├── tests/
│   ├── macros/
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
│   ├── postgres/init/
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

La primera ejecución descarga las imágenes base (~1.5 GB) y construye la imagen de Airflow. Tarda entre 5 y 15 minutos según la conexión. Las ejecuciones posteriores son casi instantáneas.

### Paso 4 — Verificar que todo está operativo

```bash
docker compose --env-file ../.env ps

curl -s http://localhost:8080/health | jq .
curl -s http://localhost:9000/minio/health/live -o /dev/null -w "MinIO: HTTP %{http_code}\n"
docker exec dip-project-postgres psql -U maritime_user -d maritime -c "\dn"
```

Salida esperada:
- Contenedores `dip-project-postgres`, `dip-airflow-postgres`, `dip-minio`, `dip-airflow-webserver`, `dip-airflow-scheduler` en estado `healthy`.
- Airflow responde `{"metadatabase": {"status": "healthy"}, "scheduler": {"status": "healthy"}}`.
- MinIO responde `HTTP 200`.
- PostgreSQL lista los esquemas `bronze`, `silver`, `gold`, `metadata`, `quarantine`, `public`.

### Paso 5 — Verificar la conexión de dbt

```bash
cd dbt/maritime
export DBT_PROFILES_DIR=~/.dbt
set -a; source ../../.env; set +a

dbt debug
```

Salida esperada: **`All checks passed!`**

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

### Quality Gate 1 — Integridad estructural (post-Bronze)
Valida columnas obligatorias, tipos de datos, nulos, duplicados, rangos, coordenadas, timestamps y schema drift. Los registros inválidos se mueven a `quarantine` con causa y regla violada.

### Quality Gate 2 — Integridad referencial (post-Silver)
Valida integridad referencial entre tablas, consistencia temporal, continuidad espacial, calidad de viajes, calidad de port calls y freshness.

### Quality Gate 3 — Calidad analítica (post-Gold)
Valida completitud, freshness, consistencia, duplicación, valores extremos, calidad de métricas y **ausencia de data leakage** en features de ML.

### Automatización de calidad

- **Ruff** — linter y formateador ultrarrápido, configurado en `pyproject.toml`.
- **mypy** — verificación estática de tipos, con `disallow_untyped_defs = true`.
- **pytest** — framework de testing con marcadores por tipo (`unit`, `integration`, `data_quality`, `slow`).
- **pre-commit** — hooks automáticos que ejecutan todas las verificaciones antes de cada commit.
- **dbt tests** — tests declarativos sobre los modelos (`not_null`, `unique`, `relationships`, `accepted_values`).

Con pre-commit y los Quality Gates activos, es imposible que un dato inválido llegue a Gold, y es imposible commitear código que no pase Ruff, mypy y los tests.

---

## 🗺️ Hoja de Ruta

### ✅ Completado — Bootstrap (Fase 1)

- [x] Estructura modular del repositorio y Data Lake local estandarizado.
- [x] Stack Docker orquestado con aislamiento de redes y volúmenes.
- [x] Configuración tipada con Pydantic Settings.
- [x] Proyecto dbt configurado con perfiles dinámicos por variables de entorno.
- [x] Calidad de código: Ruff, mypy, pytest, pre-commit.
- [x] Control de secretos y `.gitignore` validado.
- [x] Resolución de retos técnicos de bajo nivel (DNS, entrypoints, dependencias).

### 🚧 Próximos hitos

- [ ] **Ingestión de datos AIS** — primer script funcional (`ingestion/maritime/noaa_ais.py`) con Polars, checksums y metadatos.
- [ ] **Primer DAG de Airflow** — `dag_01_discovery_ingestion.py` orquestando la ingestión.
- [ ] **Modelos dbt Medallion** — staging, intermediate y primer mart de operaciones portuarias.
- [ ] **Quality Gates 1, 2 y 3** — implementados como tests dbt y validaciones Python.
- [ ] **Geofencing portuario** — detección de arrival/departure/dwell time.
- [ ] **API REST en FastAPI** — endpoints `/health`, `/ports`, `/vessels`, `/routes`, `/anomalies`.
- [ ] **Primer modelo de ML** — predicción de ETA o forecasting de congestión.
- [ ] **Capa de Intelligence** — generación de briefings operacionales con Gemini.
- [ ] **CI/CD con GitHub Actions** — lint, tests, dbt compile, DAG tests, Docker build.
- [ ] **Integración con AWS** — S3, IAM, Lambda, CloudWatch.
- [ ] **Terraform** — infraestructura como código (fuera del alcance de Fase 1).

### 🔮 Capacidad de extensión

La arquitectura está preparada para incorporar **nuevos dominios** sin rediseño: datos meteorológicos, financieros, urbanos, ambientales, científicos, gubernamentales, deportivos, industriales, o cualquier fuente pública o privada que aporte valor a la comunidad. El caso marítimo es la primera prueba, no la frontera conceptual.

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

**Data Intelligence Platform** · Fase 1 · Bootstrap completado

*Construido con rigor, documentado con honestidad, abierto a quien quiera aprender.*

</div>
