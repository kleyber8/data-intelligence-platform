# 🎯 Visión, Propósito y Principios de Diseño

## 1. El Problema: La Opacidad de las "Cajas Negras"
En la industria moderna, las plataformas de datos suelen venderse como soluciones monolíticas propietarias. El usuario final inserta datos y obtiene métricas, pero desconoce la mecánica interna: cómo se validan los datos, cómo se manejan los errores, cómo se aíslan las cargas o cómo se mitiga el sesgo. 

Esta plataforma nace desde la **Escuela de Estadística y Ciencias Actuariales (UCV)** con un objetivo de ingeniería claro: **construir un ecosistema de datos de nivel productivo donde cada componente sea auditable, reproducible y transparente.**

## 2. El Propósito: De los Datos a la Decisión
El sistema está diseñado para conectar de forma lógica y automatizada la secuencia de valor del dato:
`Datos Crudos → Información Estructurada → Análisis → Conocimiento → Inteligencia → Decisión`

Para lograr esto, el proyecto implementa una arquitectura completa que cubre:
*   Ingestión y validación estructural (Bronze).
*   Transformación, reconstrucción de entidades y enriquecimiento (Silver).
*   Modelado dimensional y agregaciones de negocio (Gold).
*   Exposición asíncrona y segura mediante API (Consumo).

## 3. El Caso de Estudio: Tráfico Marítimo (AIS)
Para probar la arquitectura, se utiliza el dominio del **Automatic Identification System (AIS)**. No es una elección aleatoria: el tráfico marítimo presenta desafíos técnicos extremos que ponen a prueba el diseño:
*   **Alta dimensionalidad:** Coordenadas geoespaciales, timestamps, velocidad, rumbo, identificadores de embarcaciones.
*   **Series temporales irregulares:** La frecuencia de reporte varía drásticamente (segundos si el barco navega, horas si está fondeado).
*   **Ruido en sensores:** Los GPS marítimos tienen márgenes de error que requieren limpieza (resuelto con Filtro de Kalman).

**La arquitectura es agnóstica al dominio.** El caso AIS es el banco de pruebas (*testbed*), pero los componentes subyacentes están diseñados para ingerir datos financieros, meteorológicos o de cualquier otra índole sin necesidad de reescribir la lógica core.

## 4. Pilares Arquitectónicos y de Gobernanza

El desarrollo no se rige por intuiciones, sino por los siguientes principios formales de ingeniería:

| Principio | Implementación Técnica |
| :--- | :--- |
| **Inmutabilidad** | Los datos en la capa Landing y Bronze nunca se modifican *in-place*. Solo se agregan nuevos archivos o registros. |
| **Contratos de Datos** | La transición entre capas está bloqueada por *Quality Gates*. Si los datos no cumplen el contrato de esquema, se aíslan. |
| **Trazabilidad Inmutable** | Uso de `ingestion_run_id` (UUIDv4) desde el archivo fuente hasta la API. El linaje es absoluto. |
| **Assume Breach & Least Privilege** | La seguridad se diseña asumiendo vulnerabilidades. El acceso a la base de datos se segmenta en 4 roles (RBAC). |
| **Local-First + Cloud-Where-Useful** | Toda la plataforma corre localmente en Docker. La nube (AWS) se integrará solo donde aporte valor real (escalabilidad, persistencia). |

## 5. Alcance y Delimitación

*   **Dentro del Alcance (Fases 1 a 6):** Pipeline Medallion completo, 3 Quality Gates, RBAC, Filtro de Kalman, API REST con JWT y documentación modular.
*   **Trabajo Futuro:** Procesamiento en *streaming* (Kafka/Flink), aprovisionamiento con Terraform (IaC), integración con Snowflake y modelos generativos con LLMs.

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
