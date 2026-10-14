-- ============================================================
-- init_rbac_roles.sql — RBAC con Least Privilege
-- ============================================================
-- Aplica el principio de Least Privilege creando 4 usuarios
-- separados por función. Elimina la dependencia del usuario
-- único (maritime_user) para todas las operaciones.
--
-- Uso:
--   docker exec -i dip-project-postgres psql \
--     -U maritime_user -d maritime \
--     -v pipeline_pass="'...'" \
--     -v dbt_pass="'...'" \
--     -v api_pass="'...'" \
--     -v analyst_pass="'...'" \
--     < scripts/security/init_rbac_roles.sql
-- ============================================================

\set ON_ERROR_STOP on

-- ---------- Eliminar usuarios previos si existen ----------
DROP ROLE IF EXISTS pipeline_user;
DROP ROLE IF EXISTS dbt_user;
DROP ROLE IF EXISTS api_user;
DROP ROLE IF EXISTS analyst_user;

-- ---------- Crear los cuatro usuarios ----------
CREATE USER pipeline_user  WITH PASSWORD :pipeline_pass  NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE USER dbt_user       WITH PASSWORD :dbt_pass       NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE USER api_user       WITH PASSWORD :api_pass       NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE USER analyst_user   WITH PASSWORD :analyst_pass   NOSUPERUSER NOCREATEDB NOCREATEROLE;

-- ============================================================
-- pipeline_user: escribe Bronze, Cuarentena, Metadata
-- ============================================================
GRANT USAGE ON SCHEMA bronze, silver, gold, metadata, quarantine TO pipeline_user;

GRANT SELECT, INSERT, UPDATE ON ALL TABLES    IN SCHEMA bronze     TO pipeline_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES    IN SCHEMA quarantine TO pipeline_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES    IN SCHEMA metadata   TO pipeline_user;
GRANT SELECT                 ON ALL TABLES    IN SCHEMA silver     TO pipeline_user;
GRANT SELECT                 ON ALL TABLES    IN SCHEMA gold       TO pipeline_user;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bronze     TO pipeline_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA quarantine TO pipeline_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA metadata   TO pipeline_user;

-- ============================================================
-- dbt_user: lee todo, escribe Silver y Gold
-- ============================================================
GRANT USAGE ON SCHEMA bronze, silver, gold, metadata, quarantine TO dbt_user;

GRANT SELECT ON ALL TABLES IN SCHEMA bronze     TO dbt_user;
GRANT SELECT ON ALL TABLES IN SCHEMA metadata   TO dbt_user;
GRANT SELECT ON ALL TABLES IN SCHEMA quarantine TO dbt_user;

GRANT CREATE, USAGE ON SCHEMA silver TO dbt_user;
GRANT CREATE, USAGE ON SCHEMA gold   TO dbt_user;

GRANT ALL ON ALL TABLES    IN SCHEMA silver TO dbt_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA silver TO dbt_user;
GRANT ALL ON ALL TABLES    IN SCHEMA gold   TO dbt_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA gold   TO dbt_user;

-- ============================================================
-- api_user: SOLO LECTURA sobre Gold
-- ============================================================
GRANT USAGE ON SCHEMA gold TO api_user;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO api_user;

-- ============================================================
-- analyst_user: SOLO LECTURA sobre Gold (idéntico a api_user)
-- ============================================================
GRANT USAGE ON SCHEMA gold TO analyst_user;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO analyst_user;

-- ============================================================
-- Default privileges para objetos futuros creados por maritime_user
-- ============================================================
ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA bronze
    GRANT SELECT, INSERT, UPDATE ON TABLES TO pipeline_user;

ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA quarantine
    GRANT SELECT, INSERT, UPDATE ON TABLES TO pipeline_user;

ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA metadata
    GRANT SELECT, INSERT, UPDATE ON TABLES TO pipeline_user;

ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA silver
    GRANT SELECT ON TABLES TO pipeline_user;

ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA gold
    GRANT SELECT ON TABLES TO pipeline_user;

ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA silver
    GRANT ALL ON TABLES TO dbt_user;

ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA gold
    GRANT ALL ON TABLES TO dbt_user;

ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA gold
    GRANT SELECT ON TABLES TO api_user;

ALTER DEFAULT PRIVILEGES FOR ROLE maritime_user IN SCHEMA gold
    GRANT SELECT ON TABLES TO analyst_user;

-- ============================================================
-- Confirmación
-- ============================================================
\echo '✅ RBAC aplicado: pipeline_user, dbt_user, api_user, analyst_user'
