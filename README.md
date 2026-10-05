# Data Intelligence Platform

Proyecto de ingeniería de datos enfocado en el ciclo de vida completo del dato: desde la ingesta hasta la inteligencia. Implementa arquitectura Medallion, Quality Gates, dbt, Airflow, FastAPI y MLOps.

**Caso de estudio inicial:** Tráfico marítimo (AIS).

## Estructura del Proyecto

- `architecture/`: Diagramas y documentación de diseño.
- `data/`: Data Lake local (raw, bronze, silver, gold, quarantine).
- `ingestion/`: Scripts de extracción de fuentes externas.
- `src/`: Código fuente modular (validación, geospatial, tracking, ML).
- `airflow/`: DAGs y configuración del orquestador.
- `dbt/`: Modelos de transformación analítica.
- `api/`: Servicios FastAPI.
- `tests/`: Pruebas unitarias, de integración y calidad de datos.
- `docker/`: Stack de desarrollo local (Postgres, MinIO, Airflow).

## Configuración Rápida

1. Copiar variables de entorno: `cp .env.example .env`
2. Crear entorno virtual: `python3 -m venv .venv && source .venv/bin/activate`
3. Instalar dependencias: `pip install -r requirements-dev.txt`
4. Levantar servicios: `cd docker && docker compose up -d`
