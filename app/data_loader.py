"""
data_loader.py — Data access layer for Streamlit in Snowflake (SiS).
Uses the active Snowpark session to query ANALYTICS views.
"""

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

_session = get_active_session()


@st.cache_data(ttl=600)
def load_unified_ads():
    df = _session.sql("SELECT * FROM IMPROVADO_ADS.ANALYTICS.UNIFIED_ADS").to_pandas()
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=600)
def load_daily_summary():
    df = _session.sql("SELECT * FROM IMPROVADO_ADS.ANALYTICS.DAILY_PLATFORM_SUMMARY").to_pandas()
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=600)
def load_campaign_performance():
    df = _session.sql("SELECT * FROM IMPROVADO_ADS.ANALYTICS.CAMPAIGN_PERFORMANCE").to_pandas()
    df.columns = [c.lower() for c in df.columns]
    return df


@st.cache_data(ttl=600)
def load_platform_summary():
    df = _session.sql("SELECT * FROM IMPROVADO_ADS.ANALYTICS.PLATFORM_SUMMARY").to_pandas()
    df.columns = [c.lower() for c in df.columns]
    return df


@st.cache_data(ttl=600)
def load_weekly_trends():
    df = _session.sql("SELECT * FROM IMPROVADO_ADS.ANALYTICS.WEEKLY_TRENDS").to_pandas()
    df.columns = [c.lower() for c in df.columns]
    df["week_start"] = pd.to_datetime(df["week_start"])
    return df


@st.cache_data(ttl=600)
def load_tiktok_funnel():
    df = _session.sql("SELECT * FROM IMPROVADO_ADS.ANALYTICS.TIKTOK_VIDEO_FUNNEL").to_pandas()
    df.columns = [c.lower() for c in df.columns]
    return df


@st.cache_data(ttl=600)
def load_google_quality():
    df = _session.sql("SELECT * FROM IMPROVADO_ADS.ANALYTICS.GOOGLE_QUALITY_ANALYSIS").to_pandas()
    df.columns = [c.lower() for c in df.columns]
    return df
