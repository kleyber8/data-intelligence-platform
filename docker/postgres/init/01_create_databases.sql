-- ============================================================
-- Data Intelligence Platform — Inicialización del proyecto
-- Ejecutado automáticamente por la imagen oficial de Postgres
-- la primera vez que se levanta el contenedor.
-- ============================================================

-- Esquemas Medallion + auxiliares
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS metadata;
CREATE SCHEMA IF NOT EXISTS quarantine;

-- Extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
