-- =============================================================================
-- 01_setup.sql — Database, Schema, Raw Tables, File Format, Stage
-- Improvado Senior Marketing Analyst Assignment
--
-- Run: snow --config-file config.toml sql -f 01_setup.sql -c improvado --database "" --schema ""
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- Database & Schema
-- ─────────────────────────────────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS IMPROVADO_ADS;
USE DATABASE IMPROVADO_ADS;

CREATE SCHEMA IF NOT EXISTS RAW;
USE SCHEMA RAW;

-- ─────────────────────────────────────────────────────────────────────────────
-- File Format (for CSV loading)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FILE FORMAT CSV_FORMAT
    TYPE = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    NULL_IF = ('', 'NULL', 'null')
    TRIM_SPACE = TRUE;

-- ─────────────────────────────────────────────────────────────────────────────
-- Internal Stage (for PUT + COPY INTO)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE STAGE ADS_STAGE
    FILE_FORMAT = CSV_FORMAT;

-- ─────────────────────────────────────────────────────────────────────────────
-- Raw Tables
-- ─────────────────────────────────────────────────────────────────────────────

-- Facebook Ads (13 columns)
CREATE OR REPLACE TABLE FACEBOOK_ADS (
    date             DATE,
    campaign_id      VARCHAR(50),
    campaign_name    VARCHAR(200),
    ad_set_id        VARCHAR(50),
    ad_set_name      VARCHAR(200),
    impressions      INT,
    clicks           INT,
    spend            DECIMAL(12,2),
    conversions      INT,
    video_views      INT,
    engagement_rate  DECIMAL(10,4),
    reach            INT,
    frequency        DECIMAL(10,2)
);

-- Google Ads (14 columns)
CREATE OR REPLACE TABLE GOOGLE_ADS (
    date                    DATE,
    campaign_id             VARCHAR(50),
    campaign_name           VARCHAR(200),
    ad_group_id             VARCHAR(50),
    ad_group_name           VARCHAR(200),
    impressions             INT,
    clicks                  INT,
    cost                    DECIMAL(12,2),
    conversions             INT,
    conversion_value        DECIMAL(12,2),
    ctr                     DECIMAL(10,4),
    avg_cpc                 DECIMAL(10,2),
    quality_score           INT,
    search_impression_share DECIMAL(10,2)
);

-- TikTok Ads (17 columns)
CREATE OR REPLACE TABLE TIKTOK_ADS (
    date            DATE,
    campaign_id     VARCHAR(50),
    campaign_name   VARCHAR(200),
    adgroup_id      VARCHAR(50),
    adgroup_name    VARCHAR(200),
    impressions     INT,
    clicks          INT,
    cost            DECIMAL(12,2),
    conversions     INT,
    video_views     INT,
    video_watch_25  INT,
    video_watch_50  INT,
    video_watch_75  INT,
    video_watch_100 INT,
    likes           INT,
    shares          INT,
    comments        INT
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Analytics Schema (for unified model and views)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS ANALYTICS;
