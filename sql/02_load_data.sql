-- =============================================================================
-- 02_load_data.sql — Stage files and load into raw tables
-- Improvado Senior Marketing Analyst Assignment
--
-- IMPORTANT: Before running this script, PUT the CSV files to the stage:
--
--   snow --config-file config.toml stage put data/01_facebook_ads.csv @IMPROVADO_ADS.RAW.ADS_STAGE --overwrite -c improvado
--   snow --config-file config.toml stage put data/02_google_ads.csv @IMPROVADO_ADS.RAW.ADS_STAGE --overwrite -c improvado
--   snow --config-file config.toml stage put data/03_tiktok_ads.csv @IMPROVADO_ADS.RAW.ADS_STAGE --overwrite -c improvado
--
-- Then run this script:
--   snow --config-file config.toml sql -f sql/02_load_data.sql -c improvado
-- =============================================================================

USE DATABASE IMPROVADO_ADS;
USE SCHEMA RAW;

-- ─────────────────────────────────────────────────────────────────────────────
-- Truncate tables (idempotent reloads)
-- ─────────────────────────────────────────────────────────────────────────────
TRUNCATE TABLE IF EXISTS FACEBOOK_ADS;
TRUNCATE TABLE IF EXISTS GOOGLE_ADS;
TRUNCATE TABLE IF EXISTS TIKTOK_ADS;

-- ─────────────────────────────────────────────────────────────────────────────
-- COPY INTO from stage
-- ─────────────────────────────────────────────────────────────────────────────

COPY INTO FACEBOOK_ADS
FROM @ADS_STAGE/01_facebook_ads.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO GOOGLE_ADS
FROM @ADS_STAGE/02_google_ads.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO TIKTOK_ADS
FROM @ADS_STAGE/03_tiktok_ads.csv
FILE_FORMAT = CSV_FORMAT
ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- Validate row counts
-- ─────────────────────────────────────────────────────────────────────────────
SELECT 'FACEBOOK_ADS' AS table_name, COUNT(*) AS row_count FROM FACEBOOK_ADS
UNION ALL
SELECT 'GOOGLE_ADS',  COUNT(*) FROM GOOGLE_ADS
UNION ALL
SELECT 'TIKTOK_ADS',  COUNT(*) FROM TIKTOK_ADS;
