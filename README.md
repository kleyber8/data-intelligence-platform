<div align="center">

# 🏛️ Data Intelligence Platform

### Infraestructura abierta para el ciclo de vida completo del dato: desde la ingesta cruda hasta la API de consumo.

**De los datos a la decisión, sin cajas negras.**

[![Arquitectura](https://img.shields.io/badge/arquitectura-Medallion-1f7a8c?style=for-the-badge&logo=databricks)](#)
[![Estado](https://img.shields.io/badge/estado-Fase%206%20%C2%B7%20API%20REST%20validada-2f855a?style=for-the-badge&logo=fastapi)](#)
[![Seguridad](https://img.shields.io/badge/seguridad-JWT%20%26%20RBAC-c53030?style=for-the-badge&logo=jsonwebtokens)](#)
[![Stack](https://img.shields.io/badge/stack-Python%20%7C%20Docker%20%7C%20dbt%20%7C%20Airflow-0f2942?style=for-the-badge&logo=apacheairflow)](#)
[![Licencia](https://img.shields.io/badge/licencia-MIT-5b6b7a?style=for-the-badge)](#)

</div>

---

## 🛠️ El "Por Qué": Ingeniería Demostrable vs. Cajas Negras

Este proyecto nace desde la Escuela de Estadística y Ciencias Actuariales (UCV) con un objetivo técnico claro: **demostrar cómo funciona una plataforma de datos real de extremo a extremo**, huyendo de las soluciones propietarias que ocultan su mecánica. 

No es solo un ejercicio académico; es una implementación de nivel productivo que expone el ciclo de vida del dato: `Datos → Información → Análisis → Conocimiento → Inteligencia → Decisión`. Utilizando el tráfico marítimo (AIS) como banco de pruebas, la arquitectura está desacoplada del dominio y diseñada bajo estrictos **principios de diseño e ingeniería**:

*   **Inmutabilidad y Contratos de Datos:** Los datos en Landing y Bronze nunca se alteran. Cada transición entre capas está regida por *Quality Gates* y validaciones declarativas (dbt).
*   **Trazabilidad Absoluta:** Cada registro cuenta con un `ingestion_run_id` y `ingestion_row_id`, permitiendo auditar el linaje desde el archivo original hasta la API final.
*   **Aislamiento de Recursos:** Orquestación local *Local-First* (Docker, MinIO) lista para migrar a Cloud (*Cloud-Where-Useful*).
*   **Assume Breach & Least Privilege:** Postura técnica donde la seguridad se asume vulnerada en el diseño. Cuatro roles dedicados en base de datos (RBAC) garantizan que la API solo lea la capa Gold.

---

## ⚡ Estado de Avance: 6 Fases Cerradas y Validadas

El pipeline no es teórico. Cuenta con un entorno local *end-to-end* validado mediante pruebas automatizadas y Quality Gates.

| Fase | Hito Arquitectónico | Validación Técnica |
| :--- | :--- | :--- |
| **1** | 🏗️ **Bootstrap & Docker** | Entorno orquestado (Postgres, Airflow, MinIO, dbt) con aislamiento estricto de redes y secretos. |
| **2** | 🥉 **Ingestión & Bronze** | Extracción AIS (Polars), checksums SHA-256. **QG1:** 170 registros validados, 30 en cuarentena (JSONB). |
| **3** | 🥈 **Capa Silver & dbt** | Modelos (Haversine, Tracks). **17 tests dbt** en verde. **QG2:** 0 violaciones de integridad. |
| **4** | 🥇 **Capa Gold & RBAC** | **7 Data Marts** analíticos. **QG3:** Validación *cross-layer*. **RBAC:** 4 usuarios con *Least Privilege*. |
| **5** | 🧠 **Rigor Matemático** | Filtro de Kalman 4D (suavizado GPS), resampling temporal y *feature prep* sin *data leakage*. |
| **6** | 🔌 **API REST (FastAPI)** | Fachada asíncrona con **JWT**, *Rate Limiting*, validación Pydantic y conexión restringida a Gold. |

---

## 📚 Portal de Documentación Modular

Para mantener una base de código mantenible y una lectura sin sobrecarga cognitiva, la arquitectura y decisiones están divididas en manuales técnicos dentro de la carpeta `documentation/`:

| Icono | Documento | Propósito |
| :---: | :--- | :--- |
| 🎯 | **[Visión y Principios](./documentation/01_vision_purpose.md)** | Los fundamentos de ingeniería, el caso de uso y el modelo de colaboración. |
| 🏛️ | **[Arquitectura de Referencia](./documentation/02_architecture.md)** | El flujo Medallion, la pila tecnológica y los Quality Gates. |
| 📊 | **[Estado y Fases](./documentation/03_status_phases.md)** | Radiografía técnica de las 6 fases y métricas de ejecución. |
| 🔒 | **[Seguridad y RBAC](./documentation/04_security_roadmap.md)** | Postura de seguridad, trayectoria evolutiva y *Least Privilege*. |
| 🎯 | **[Calidad y Gobernanza](./documentation/05_quality_governance.md)** | Contratos de datos, linaje y la Triple Barrera de Calidad. |
| 🚀 | **[Guía de Inicio Rápido](./documentation/06_quickstart_guide.md)** | El paso a paso en terminal para levantar toda la plataforma en Fedora. |
| 🗺️ | **[Hoja de Ruta (Roadmap)](./documentation/07_roadmap.md)** | Próximos hitos: ML Avanzado, LLMs con Gemini, AWS y Snowflake. |

---

## 🖥️ Panel de Control: Interfaces Gráficas

Una vez desplegado el stack local (`docker compose up -d`), el control y la observabilidad del sistema se materializan en interfaces visuales:

| Interfaz | URL Local | Credenciales | Propósito Operativo |
| :--- | :--- | :--- | :--- |
| 🌪️ **Apache Airflow** | `http://localhost:8080` | `admin` / `admin` | Orquestación de DAGs y monitoreo de ejecuciones. |
| ⚡ **FastAPI Swagger** | `http://localhost:8001/docs` | *(JWT Auth)* | Explorador interactivo de la API REST de la capa Gold. |
| 🗄️ **MinIO Console** | `http://localhost:9001` | `minioadmin` / `minioadmin` | Navegador del Data Lake (Buckets S3 y archivos Parquet). |
| 🐘 **pgAdmin** | `http://localhost:5050` | `admin@example.com` / `admin` | Administración e inspección gráfica de PostgreSQL. |
| 📊 **dbt Docs** | `./scripts/serve_dbt_docs.sh` | *(Automático)* | Catálogo visual y grafo de linaje de las transformaciones. |
| 🐳 **Portainer** | `https://localhost:9443` | *(Configurar)* | Observabilidad de contenedores Docker (CPU/RAM). |

---

## 🤝 Contribución y Transferencia de Conocimiento

Este repositorio es un espacio abierto para la ingeniería y la experimentación. El verdadero valor educativo no reside únicamente en el código funcional, sino en la documentación explícita de las decisiones arquitectónicas (bajo el esquema: *problema → alternativas → decisión → justificación → consecuencias*). 

Se invita a estudiantes, docentes e ingenieros a clonar el proyecto, auditar los pipelines y proponer mejoras. Consulta la **[Guía de Inicio Rápido](./documentation/06_quickstart_guide.md)** para configurar el entorno.

## 📄 Licencia

Distribuido bajo la **Licencia MIT**. Consulta [`LICENSE`](./LICENSE) para más detalles.

---

<div align="center">
<i>Construido con rigor de ingeniería, documentado con honestidad técnica, abierto a quien quiera aprender.</i>
<br>
<b>Data Intelligence Platform · Fase 6 · 2026</b>
</div>
