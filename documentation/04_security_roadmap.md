# 🔒 Trayectoria de Seguridad y RBAC (Least Privilege)

En una plataforma de datos, la seguridad no es un producto que se instala al final; es una **propiedad emergente del diseño**. Bajo la premisa **Assume Breach** (asumir que algún componente será vulnerado), este proyecto implementa múltiples capas de defensa para garantizar la integridad del pipeline y la confidencialidad de los datos.

## 1. La Matriz de Seguridad Evolutiva

La postura de seguridad maduró junto con la arquitectura en cada fase:

| Fase | Vector de Amenaza | Medida de Mitigación Implementada |
| :--- | :--- | :--- |
| **1. Bootstrap** | Fuga de secretos en el repositorio. | `.env` excluido vía `.gitignore`. Plantilla pública `.env.example`. Contenedores en red bridge aislada. |
| **2. Bronze** | Inyección SQL (SQLi) y manipulación de archivos. | SQLAlchemy con **parámetros vinculados** (`text()`). Checksums SHA-256 para validar inmutabilidad del Parquet. |
| **3. Silver** | Alteración de configuraciones críticas. | Montaje de perfiles dbt en modo *Read-Only* (`:ro`). Aislamiento de dependencias en `/opt/dbt-venv`. |
| **4. Gold** | Acceso no autorizado a datos sensibles. | **RBAC en PostgreSQL:** 4 roles dedicados. `api_user` aislado estrictamente a la capa Gold. |
| **5. Matemáticas** | Sesgo algorítmico y *data leakage*. | Test de Chi-cuadrado/Gini en cuarentena. Split temporal estricto en preparación de features. |
| **6. API REST** | Abuso de endpoints y robo de sesión. | **JWT** (expiración 30m), **Rate Limiting** (`slowapi`) y validación estricta con Pydantic. |

## 2. El Principio de Menor Privilegio (RBAC)

El error más común en ingeniería de datos es usar un superusuario (como `postgres` o `maritime_user`) para todo. En la Fase 4, aplicamos un modelo de roles estricto en PostgreSQL para contener el radio de daño.

### 2.1. Matriz de Roles y Permisos

| Rol (Usuario) | Función en el Pipeline | Permisos en Base de Datos |
| :--- | :--- | :--- |
| **`pipeline_user`** | Scripts de Ingesta Python. | `INSERT`, `UPDATE`, `SELECT` en `bronze`, `metadata` y `quarantine`. `SELECT` en `silver`/`gold`. |
| **`dbt_user`** | Transformaciones analíticas. | `SELECT` en `bronze`. `CREATE`, `ALTER`, `DROP` y `ALL` en `silver` y `gold`. |
| **`api_user`** | API REST (FastAPI). | **Exclusivamente `SELECT` en `gold`.** Cero acceso a capas internas. |
| **`analyst_user`** | Análisis ad-hoc / BI. | **Exclusivamente `SELECT` en `gold`.** |

### 2.2. Prueba Empírica de Contención

Si un atacante comprometiera la API y robara las credenciales de `api_user`, el Principio de Menor Privilegio bloquea su movimiento lateral:

```sql
-- Intentando leer la capa Silver con api_user
SELECT COUNT(*) FROM silver.int_vessel_tracks;

-- RESULTADO:
ERROR: permission denied for schema silver
```

## 3. Defensas en la Capa de Consumo (API REST)

La API implementa seguridad stateless (sin estado) y validación estricta de límites:

*   **JWT (JSON Web Tokens):** Autenticación criptográfica firmada con HS256. El token expira en 30 minutos para minimizar el riesgo si es interceptado.
*   **Rate Limiting:** Middleware `slowapi` limita el número de peticiones por IP. Previene ataques de Fuerza Bruta contra el endpoint de `/token` y denegación de servicio (DoS).
*   **Validación Pydantic:** Cualquier petición que no cumpla el contrato de tipos (ej. enviar texto en un campo de latitud) es rechazada con un `HTTP 422 Unprocessable Entity` antes de tocar la base de datos.

## 4. Trayectoria Futura de Seguridad (Roadmap)

La arquitectura está diseñada para escalar su seguridad hacia la nube:

*   **Fase 7 (ML):** Monitoreo de *Model Drift* (evitar degradación de predicciones). Explicabilidad con SHAP para auditar cajas negras.
*   **Fase 8 (LLMs):** Sanitización de *prompts* para evitar inyecciones de IA. Auditoría de alucinaciones mediante validación de métricas en origen.
*   **Fase 9 (CI/CD):** GitHub Secrets para credenciales. Análisis estático (SAST) y escaneo de dependencias (Dependabot).
*   **Fase 10 (AWS):** Uso de **AWS Secrets Manager** (rotación automática de credenciales), VPC privada para bases de datos y cifrado KMS para volúmenes EBS/S3.
*   **Fase 11 (Terraform):** *State* de Terraform cifrado en S3 para evitar exposición de infraestructura.
*   **Fase 12 (Snowflake):** Implementación de *Row-Level Security* y enmascaramiento de datos (Data Masking) para PII.

## 5. El Principio Rector

> **La seguridad no es un producto que se instala, es una postura de ingeniería que se diseña.**

Ningún firewall externo hace un sistema seguro. Lo que lo hace seguro es asumir que cada componente fallará, aislar los recursos, aplicar el mínimo privilegio y auditar cada movimiento.

---
*Documento mantenido bajo el esquema: problema → alternativas → decisión → justificación → consecuencias.*
