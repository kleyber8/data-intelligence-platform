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

No es solo un ejercicio académico; es una implementación de nivel productivo que expone el ciclo de vida del dato en su totalidad: `Datos → Información → Análisis → Conocimiento → Inteligencia → Decisión`. Utilizando el tráfico marítimo (AIS) como banco de pruebas, hemos diseñado una arquitectura desacoplada del dominio, pensada para que otros estudiantes e ingenieros puedan estudiarla, reproducirla y expandirla.

Buscamos demostrar que la transparencia técnica y el uso de herramientas open-source (como Airflow, dbt y FastAPI) pueden igualar el rigor de las plataformas empresariales más complejas. Nuestros pilares de diseño son:

*   **Inmutabilidad y Contratos de Datos:** Los datos en Landing y Bronze nunca se alteran. Cada transición entre capas está regida por *Quality Gates* y validaciones declarativas (dbt).
*   **Trazabilidad Absoluta:** Cada registro cuenta con un `ingestion_run_id` y `ingestion_row_id`, permitiendo auditar el linaje desde el archivo original hasta la API final.
*   **Aislamiento de Recursos:** Orquestación local *Local-First* (Docker, MinIO) lista para migrar a Cloud (*Cloud-Where-Useful*).
*   **Seguridad por Diseño (Assume Breach):** Cuatro roles dedicados en base de datos (RBAC) garantizan que la API solo tenga acceso a la capa de consumo (Gold), minimizando el radio de acción ante cualquier fallo.

---

## ⚡ Estado de Avance: 6 Fases Cerradas y Validadas

El pipeline no es teoría. Cuenta con un entorno local *end-to-end* validado mediante pruebas automatizadas y Quality Gates.

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

Para mantener el código mantenible y una lectura sin sobrecarga cognitiva, la arquitectura y las decisiones están divididas en manuales técnicos dentro de la carpeta `documentation/`:

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
<b>Data Intelligence Platform · Fase 6 · 2026</b>
</div>
