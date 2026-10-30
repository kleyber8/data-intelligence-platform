# 🗺️ Hoja de Ruta (Roadmap) y Trabajo Futuro

El proyecto está diseñado bajo una arquitectura altamente extensible. La culminación de la Fase 6 (API REST) marca el final de la infraestructura base y el comienzo de la capa de consumo avanzado. 

Las siguientes fases (7 a 12) representan la evolución natural del ecosistema: desde la analítica descriptiva hasta la inteligencia predictiva y el despliegue Cloud-native.

## Fase 7: Machine Learning Avanzado y Detección de Anomalías
**Objetivo:** Transformar los datos históricos de Gold en modelos predictivos.
*   **Modelos Predictivos:**
    *   *ETA Prediction:* Estimar el tiempo de llegada de embarcaciones usando variables de distancia, tipo de barco, clima y congestión histórica.
    *   *Congestion Forecasting:* Predecir la saturación portuaria a 6h y 24h usando series temporales.
*   **Detección de Anomalías No Supervisada:** Implementación de *Isolation Forest* y *DBSCAN* para detectar comportamientos anómalos (desvíos de ruta, apagones de GPS) no contemplados por reglas estáticas.
*   **Explicabilidad (XAI):** Uso de **SHAP** para auditar las predicciones de los modelos y garantizar que no operen como "cajas negras".
*   **Integración:** Uso del pipeline `feature_prep.py` (creado en la Fase 5) con split temporal estricto para evitar *data leakage*.

## Fase 8: Capa de Inteligencia Operativa (LLMs)
**Objetivo:** Generar informes operacionales (Briefings) en lenguaje natural.
*   **Integración con Google Gemini:** Uso de la API de Gemini para redactar resúmenes ejecutivos diarios a partir de los eventos estructurados de la capa Gold (ej. "El puerto de Rotterdam alcanzó nivel crítico de congestión a las 14:00, impulsado por 15 barcos de carga").
*   **Mitigación de Alucinaciones:** El LLM no consulta la base de datos cruda ni genera texto libre desde cero. Recibe un *prompt* inyectado con métricas exactas (JSON estructurado) y su tarea es únicamente redactar.
*   **Trazabilidad:** Cada briefing generado almacenará metadatos sobre qué modelo se usó, qué versión del *prompt* y qué IDs de eventos de origen alimentaron el texto.

## Fase 9: CI/CD y Automatización de Calidad
**Objetivo:** Garantizar que cualquier contribución al repositorio no rompa el pipeline (Integración Continua).
*   **GitHub Actions:** Pipeline automatizado en cada `git push` o `pull_request`.
*   **Etapas del Pipeline:**
    *   `ruff` (Linter) y `mypy` (Tipado).
    *   `pytest` (Tests unitarios y de integración).
    *   `dbt compile` y `dbt test` (Validar contratos de datos).
    *   `docker build` (Asegurar que las imágenes compilan).
*   **Análisis de Seguridad:** Escaneo de dependencias vulnerables con Dependabot y análisis estático de código (SAST).

## Fase 10: Infraestructura Cloud (AWS)
**Objetivo:** Migrar el ecosistema *Local-First* a un entorno *Cloud-Where-Useful* productivo.
*   **Almacenamiento:** Migración del Data Lake local (MinIO) a **AWS S3**, utilizando cifrado KMS y políticas de ciclo de vida para archivar datos crudos antiguos.
*   **Seguridad:** Implementación de **AWS Secrets Manager** para eliminar las variables de entorno en texto plano. Uso de roles **IAM** estrictos para que los servicios (ej. Lambda, EC2) se comuniquen entre sí sin contraseñas estáticas.
*   **Procesamiento Serverless:** Uso de **AWS Lambda** y **CloudWatch** para ejecutar tareas de monitoreo de datos o ingestas de bajo volumen bajo demanda.
*   **Redes:** Configuración de **VPC privadas**, subnets y Security Groups para aislar las bases de datos PostgreSQL del internet público.

## Fase 11: Infrastructure as Code (Terraform)
**Objetivo:** Desplegar y versionar toda la infraestructura Cloud de forma declarativa.
*   **Terraform:** Toda la infraestructura de AWS (S3, RDS, IAM, Lambdas) se definirá en archivos `.tf`.
*   **Beneficios:** Reproducibilidad total. En lugar de crear servidores a mano, se ejecuta `terraform apply` para levantar el entorno de producción en minutos. El *state* de Terraform se guardará cifrado en S3 para evitar modificaciones manuales no autorizadas.

## Fase 12: Migración Analítica a Snowflake
**Objetivo:** Evaluar el rendimiento de un Data Warehouse Cloud moderno frente a PostgreSQL local.
*   **Migración:** Replicar los modelos de dbt (Silver y Gold) para que se ejecuten sobre Snowflake.
*   **Comparación Arquitectónica:** Experimentar con diferentes estrategias de Snowflake:
    1.  *Airflow + dbt + Snowflake* (Enfoque tradicional ELT).
    2.  *Snowflake Streams + Tasks* (Orquestación nativa en el DW).
    3.  *Snowflake Dynamic Tables* (Materialización automática).
*   **Gobernanza:** Aplicación de *Row-Level Security* (RLS) para que diferentes usuarios analíticos vean solo sus datos, y *Data Masking* para ocultar información sensible (PII).

---

## El Futuro del Proyecto: Extensibilidad

El límite del proyecto no es el tráfico marítimo. La arquitectura desacoplada permite incorporar nuevas fuentes y dominios sin rediseñar el core:
*   Datos financieros o bursátiles.
*   Datos meteorológicos para correlacionar con la congestión portuaria.
*   Datos urbanos (sensores IoT).
*   Procesamiento en tiempo real (*streaming* con Kafka) para reemplazar el procesamiento batch actual.

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
