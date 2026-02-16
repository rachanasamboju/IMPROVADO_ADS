-- =============================================================================
-- 03_unified_model.sql — Unified cross-platform model + analytical views
-- Improvado Senior Marketing Analyst Assignment
--
-- Run: snow --config-file config.toml sql -f 03_unified_model.sql -c improvado
-- =============================================================================

USE DATABASE IMPROVADO_ADS;

-- ─────────────────────────────────────────────────────────────────────────────
-- UNIFIED_ADS — Master view combining all 3 platforms
--
-- Normalizes column names, computes standard KPIs, and preserves
-- platform-specific metrics as nullable columns.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW ANALYTICS.UNIFIED_ADS AS

-- ── Facebook Ads ──
SELECT
    'Facebook'                                          AS platform,
    date,
    campaign_id,
    campaign_name,
    ad_set_id                                           AS ad_group_id,
    ad_set_name                                         AS ad_group_name,
    impressions,
    clicks,
    spend,
    conversions,

    -- Standard KPIs
    ROUND(clicks / NULLIF(impressions, 0), 4)           AS ctr,
    ROUND(spend / NULLIF(clicks, 0), 2)                 AS cpc,
    ROUND(spend / NULLIF(conversions, 0), 2)            AS cpa,
    ROUND(conversions / NULLIF(clicks, 0), 4)           AS conversion_rate,
    ROUND((spend / NULLIF(impressions, 0)) * 1000, 2)   AS cpm,

    -- Facebook-specific
    video_views,
    engagement_rate,
    reach,
    frequency,

    -- Google-specific (NULL)
    NULL::DECIMAL(12,2)     AS conversion_value,
    NULL::INT               AS quality_score,
    NULL::DECIMAL(10,2)     AS search_impression_share,

    -- TikTok-specific (NULL)
    NULL::INT               AS video_watch_25,
    NULL::INT               AS video_watch_50,
    NULL::INT               AS video_watch_75,
    NULL::INT               AS video_watch_100,
    NULL::INT               AS likes,
    NULL::INT               AS shares,
    NULL::INT               AS comments
FROM RAW.FACEBOOK_ADS

UNION ALL

-- ── Google Ads ──
SELECT
    'Google'                                            AS platform,
    date,
    campaign_id,
    campaign_name,
    ad_group_id,
    ad_group_name,
    impressions,
    clicks,
    cost                                                AS spend,
    conversions,

    -- Standard KPIs
    ROUND(clicks / NULLIF(impressions, 0), 4)           AS ctr,
    ROUND(cost / NULLIF(clicks, 0), 2)                  AS cpc,
    ROUND(cost / NULLIF(conversions, 0), 2)             AS cpa,
    ROUND(conversions / NULLIF(clicks, 0), 4)           AS conversion_rate,
    ROUND((cost / NULLIF(impressions, 0)) * 1000, 2)    AS cpm,

    -- Facebook-specific (NULL)
    NULL::INT               AS video_views,
    NULL::DECIMAL(10,4)     AS engagement_rate,
    NULL::INT               AS reach,
    NULL::DECIMAL(10,2)     AS frequency,

    -- Google-specific
    conversion_value,
    quality_score,
    search_impression_share,

    -- TikTok-specific (NULL)
    NULL::INT               AS video_watch_25,
    NULL::INT               AS video_watch_50,
    NULL::INT               AS video_watch_75,
    NULL::INT               AS video_watch_100,
    NULL::INT               AS likes,
    NULL::INT               AS shares,
    NULL::INT               AS comments
FROM RAW.GOOGLE_ADS

UNION ALL

-- ── TikTok Ads ──
SELECT
    'TikTok'                                            AS platform,
    date,
    campaign_id,
    campaign_name,
    adgroup_id                                          AS ad_group_id,
    adgroup_name                                        AS ad_group_name,
    impressions,
    clicks,
    cost                                                AS spend,
    conversions,

    -- Standard KPIs
    ROUND(clicks / NULLIF(impressions, 0), 4)           AS ctr,
    ROUND(cost / NULLIF(clicks, 0), 2)                  AS cpc,
    ROUND(cost / NULLIF(conversions, 0), 2)             AS cpa,
    ROUND(conversions / NULLIF(clicks, 0), 4)           AS conversion_rate,
    ROUND((cost / NULLIF(impressions, 0)) * 1000, 2)    AS cpm,

    -- Facebook-specific (NULL for TikTok, except video_views which is shared)
    video_views,
    NULL::DECIMAL(10,4)     AS engagement_rate,
    NULL::INT               AS reach,
    NULL::DECIMAL(10,2)     AS frequency,

    -- Google-specific (NULL)
    NULL::DECIMAL(12,2)     AS conversion_value,
    NULL::INT               AS quality_score,
    NULL::DECIMAL(10,2)     AS search_impression_share,

    -- TikTok-specific
    video_watch_25,
    video_watch_50,
    video_watch_75,
    video_watch_100,
    likes,
    shares,
    comments
FROM RAW.TIKTOK_ADS;


-- ─────────────────────────────────────────────────────────────────────────────
-- DAILY_PLATFORM_SUMMARY — Aggregated daily metrics per platform
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW ANALYTICS.DAILY_PLATFORM_SUMMARY AS
SELECT
    date,
    platform,
    COUNT(*)                                                AS ad_groups_active,
    SUM(impressions)                                        AS total_impressions,
    SUM(clicks)                                             AS total_clicks,
    SUM(spend)                                              AS total_spend,
    SUM(conversions)                                        AS total_conversions,
    ROUND(SUM(clicks)       / NULLIF(SUM(impressions), 0), 4)   AS avg_ctr,
    ROUND(SUM(spend)        / NULLIF(SUM(clicks), 0), 2)        AS avg_cpc,
    ROUND(SUM(spend)        / NULLIF(SUM(conversions), 0), 2)   AS avg_cpa,
    ROUND(SUM(conversions)  / NULLIF(SUM(clicks), 0), 4)        AS avg_conversion_rate,
    ROUND((SUM(spend) / NULLIF(SUM(impressions), 0)) * 1000, 2) AS avg_cpm,
    SUM(video_views)                                        AS total_video_views
FROM ANALYTICS.UNIFIED_ADS
GROUP BY date, platform
ORDER BY date, platform;


-- ─────────────────────────────────────────────────────────────────────────────
-- CAMPAIGN_PERFORMANCE — Campaign-level aggregation with rankings
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW ANALYTICS.CAMPAIGN_PERFORMANCE AS
SELECT
    platform,
    campaign_id,
    campaign_name,
    MIN(date)                                               AS first_active_date,
    MAX(date)                                               AS last_active_date,
    COUNT(DISTINCT date)                                    AS active_days,
    COUNT(DISTINCT ad_group_id)                             AS ad_groups,
    SUM(impressions)                                        AS total_impressions,
    SUM(clicks)                                             AS total_clicks,
    SUM(spend)                                              AS total_spend,
    SUM(conversions)                                        AS total_conversions,
    ROUND(SUM(clicks)       / NULLIF(SUM(impressions), 0), 4)   AS avg_ctr,
    ROUND(SUM(spend)        / NULLIF(SUM(clicks), 0), 2)        AS avg_cpc,
    ROUND(SUM(spend)        / NULLIF(SUM(conversions), 0), 2)   AS avg_cpa,
    ROUND(SUM(conversions)  / NULLIF(SUM(clicks), 0), 4)        AS avg_conversion_rate,
    ROUND((SUM(spend) / NULLIF(SUM(impressions), 0)) * 1000, 2) AS avg_cpm,
    SUM(video_views)                                        AS total_video_views,
    -- Google-specific aggregates
    SUM(conversion_value)                                   AS total_conversion_value,
    ROUND(SUM(conversion_value) / NULLIF(SUM(spend), 0), 2) AS roas,
    -- TikTok-specific aggregates
    SUM(likes)                                              AS total_likes,
    SUM(shares)                                             AS total_shares,
    SUM(comments)                                           AS total_comments,
    -- Rankings
    RANK() OVER (ORDER BY SUM(spend) DESC)                  AS spend_rank,
    RANK() OVER (ORDER BY SUM(conversions) DESC)            AS conversions_rank,
    RANK() OVER (ORDER BY SUM(spend) / NULLIF(SUM(conversions), 0) ASC) AS cpa_rank
FROM ANALYTICS.UNIFIED_ADS
GROUP BY platform, campaign_id, campaign_name
ORDER BY total_spend DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- PLATFORM_SUMMARY — High-level platform comparison
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW ANALYTICS.PLATFORM_SUMMARY AS
SELECT
    platform,
    COUNT(DISTINCT campaign_id)                             AS campaigns,
    COUNT(DISTINCT ad_group_id)                             AS ad_groups,
    COUNT(DISTINCT date)                                    AS active_days,
    SUM(impressions)                                        AS total_impressions,
    SUM(clicks)                                             AS total_clicks,
    SUM(spend)                                              AS total_spend,
    SUM(conversions)                                        AS total_conversions,
    ROUND(SUM(clicks)       / NULLIF(SUM(impressions), 0), 4)   AS avg_ctr,
    ROUND(SUM(spend)        / NULLIF(SUM(clicks), 0), 2)        AS avg_cpc,
    ROUND(SUM(spend)        / NULLIF(SUM(conversions), 0), 2)   AS avg_cpa,
    ROUND(SUM(conversions)  / NULLIF(SUM(clicks), 0), 4)        AS avg_conversion_rate,
    ROUND((SUM(spend) / NULLIF(SUM(impressions), 0)) * 1000, 2) AS avg_cpm,
    ROUND(SUM(spend) / SUM(SUM(spend)) OVER (), 4)         AS spend_share,
    ROUND(SUM(conversions) / SUM(SUM(conversions)) OVER (), 4) AS conversion_share
FROM ANALYTICS.UNIFIED_ADS
GROUP BY platform
ORDER BY total_spend DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- WEEKLY_TRENDS — Week-over-week trends per platform
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW ANALYTICS.WEEKLY_TRENDS AS
WITH weekly AS (
    SELECT
        DATE_TRUNC('WEEK', date)    AS week_start,
        platform,
        SUM(impressions)            AS impressions,
        SUM(clicks)                 AS clicks,
        SUM(spend)                  AS spend,
        SUM(conversions)            AS conversions
    FROM ANALYTICS.UNIFIED_ADS
    GROUP BY week_start, platform
)
SELECT
    week_start,
    platform,
    impressions,
    clicks,
    spend,
    conversions,
    ROUND(clicks / NULLIF(impressions, 0), 4)       AS ctr,
    ROUND(spend / NULLIF(clicks, 0), 2)             AS cpc,
    ROUND(spend / NULLIF(conversions, 0), 2)        AS cpa,
    -- Week-over-week change
    ROUND((spend - LAG(spend) OVER (PARTITION BY platform ORDER BY week_start))
        / NULLIF(LAG(spend) OVER (PARTITION BY platform ORDER BY week_start), 0), 4)
                                                    AS spend_wow_change,
    ROUND((conversions - LAG(conversions) OVER (PARTITION BY platform ORDER BY week_start))
        / NULLIF(LAG(conversions) OVER (PARTITION BY platform ORDER BY week_start), 0), 4)
                                                    AS conversions_wow_change
FROM weekly
ORDER BY week_start, platform;


-- ─────────────────────────────────────────────────────────────────────────────
-- TIKTOK_VIDEO_FUNNEL — Video completion funnel for TikTok
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW ANALYTICS.TIKTOK_VIDEO_FUNNEL AS
SELECT
    campaign_name,
    SUM(video_views)        AS total_views,
    SUM(video_watch_25)     AS watched_25pct,
    SUM(video_watch_50)     AS watched_50pct,
    SUM(video_watch_75)     AS watched_75pct,
    SUM(video_watch_100)    AS watched_100pct,
    ROUND(SUM(video_watch_25)  / NULLIF(SUM(video_views), 0), 4) AS rate_25pct,
    ROUND(SUM(video_watch_50)  / NULLIF(SUM(video_views), 0), 4) AS rate_50pct,
    ROUND(SUM(video_watch_75)  / NULLIF(SUM(video_views), 0), 4) AS rate_75pct,
    ROUND(SUM(video_watch_100) / NULLIF(SUM(video_views), 0), 4) AS rate_100pct
FROM RAW.TIKTOK_ADS
GROUP BY campaign_name
ORDER BY total_views DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- GOOGLE_QUALITY_ANALYSIS — Quality score vs performance
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW ANALYTICS.GOOGLE_QUALITY_ANALYSIS AS
SELECT
    campaign_name,
    ad_group_name,
    ROUND(AVG(quality_score), 1)                            AS avg_quality_score,
    SUM(impressions)                                        AS total_impressions,
    SUM(clicks)                                             AS total_clicks,
    SUM(cost)                                               AS total_cost,
    SUM(conversions)                                        AS total_conversions,
    SUM(conversion_value)                                   AS total_conversion_value,
    ROUND(SUM(clicks) / NULLIF(SUM(impressions), 0), 4)     AS avg_ctr,
    ROUND(SUM(cost)   / NULLIF(SUM(clicks), 0), 2)          AS avg_cpc,
    ROUND(SUM(cost)   / NULLIF(SUM(conversions), 0), 2)     AS avg_cpa,
    ROUND(SUM(conversion_value) / NULLIF(SUM(cost), 0), 2)  AS roas,
    ROUND(AVG(search_impression_share), 2)                  AS avg_search_impression_share
FROM RAW.GOOGLE_ADS
GROUP BY campaign_name, ad_group_name
ORDER BY avg_quality_score DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Validation
-- ─────────────────────────────────────────────────────────────────────────────
SELECT 'UNIFIED_ADS' AS view_name, COUNT(*) AS row_count FROM ANALYTICS.UNIFIED_ADS
UNION ALL
SELECT 'DAILY_PLATFORM_SUMMARY', COUNT(*) FROM ANALYTICS.DAILY_PLATFORM_SUMMARY
UNION ALL
SELECT 'CAMPAIGN_PERFORMANCE', COUNT(*) FROM ANALYTICS.CAMPAIGN_PERFORMANCE
UNION ALL
SELECT 'PLATFORM_SUMMARY', COUNT(*) FROM ANALYTICS.PLATFORM_SUMMARY;
