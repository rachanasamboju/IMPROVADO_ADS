import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Cross-Channel Ad Performance", layout="wide")
COLORS = {"Facebook": "#1877F2", "Google": "#34A853", "TikTok": "#000000"}

# ── Snowflake Connection ─────────────────────────────────────────────────────
@st.cache_resource
def get_snowflake_connection():
    return snowflake.connector.connect(
        account=st.secrets["connections"]["snowflake"]["account"],
        user=st.secrets["connections"]["snowflake"]["user"],
        password=st.secrets["connections"]["snowflake"]["password"],
        warehouse=st.secrets["connections"]["snowflake"]["warehouse"],
        database=st.secrets["connections"]["snowflake"]["database"],
        schema=st.secrets["connections"]["snowflake"]["schema"],
        role=st.secrets["connections"]["snowflake"]["role"],
    )

@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(query)
    df = cur.fetch_pandas_all()
    df.columns = [c.lower() for c in df.columns]
    return df


# ── Load Data ─────────────────────────────────────────────────────────────────
unified = run_query("SELECT * FROM IMPROVADO_ADS.ANALYTICS.UNIFIED_ADS")
unified["date"] = pd.to_datetime(unified["date"])

daily = run_query("SELECT * FROM IMPROVADO_ADS.ANALYTICS.DAILY_PLATFORM_SUMMARY")
daily["date"] = pd.to_datetime(daily["date"])

camp_perf = run_query("SELECT * FROM IMPROVADO_ADS.ANALYTICS.CAMPAIGN_PERFORMANCE")

plat_summary = run_query("SELECT * FROM IMPROVADO_ADS.ANALYTICS.PLATFORM_SUMMARY")

weekly = run_query("SELECT * FROM IMPROVADO_ADS.ANALYTICS.WEEKLY_TRENDS")
weekly["week_start"] = pd.to_datetime(weekly["week_start"])

tt_funnel = run_query("SELECT * FROM IMPROVADO_ADS.ANALYTICS.TIKTOK_VIDEO_FUNNEL")

gq = run_query("SELECT * FROM IMPROVADO_ADS.ANALYTICS.GOOGLE_QUALITY_ANALYSIS")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Cross-Channel Advertising Performance")
st.caption("Facebook Ads | Google Ads | TikTok Ads — Unified analytics powered by Snowflake")

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    min_d, max_d = unified["date"].min().date(), unified["date"].max().date()
    date_range = st.date_input(
        "Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d
    )
    all_plat = sorted(unified["platform"].unique())
    platforms = st.multiselect("Platform", options=all_plat, default=all_plat)
    avail_camps = sorted(
        unified[unified["platform"].isin(platforms)]["campaign_name"].unique()
    )
    campaigns = st.multiselect("Campaign", options=avail_camps, default=avail_camps)

# ── Apply Filters ─────────────────────────────────────────────────────────────
if len(date_range) == 2:
    mask = (
        (unified["date"].dt.date >= date_range[0])
        & (unified["date"].dt.date <= date_range[1])
        & (unified["platform"].isin(platforms))
        & (unified["campaign_name"].isin(campaigns))
    )
else:
    mask = unified["platform"].isin(platforms) & unified["campaign_name"].isin(
        campaigns
    )

fdf = unified[mask].copy()
if fdf.empty:
    st.warning("No data for selected filters.")
    st.stop()

daily_f = daily[daily["platform"].isin(platforms)].copy()
if len(date_range) == 2:
    daily_f = daily_f[
        (daily_f["date"].dt.date >= date_range[0])
        & (daily_f["date"].dt.date <= date_range[1])
    ]

camp_f = camp_perf[
    (camp_perf["platform"].isin(platforms))
    & (camp_perf["campaign_name"].isin(campaigns))
].copy()
plat_f = plat_summary[plat_summary["platform"].isin(platforms)].copy()
weekly_f = weekly[weekly["platform"].isin(platforms)].copy()

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(
    ["Executive Overview", "Platform Deep Dive", "Campaign Analysis", "Insights"]
)

# ── TAB 1: EXECUTIVE OVERVIEW ─────────────────────────────────────────────────
with tab1:
    total_spend = float(fdf["spend"].sum())
    total_imp = int(fdf["impressions"].sum())
    total_clicks = int(fdf["clicks"].sum())
    total_conv = int(fdf["conversions"].sum())
    avg_cpa = total_spend / total_conv if total_conv else 0
    avg_ctr = total_clicks / total_imp if total_imp else 0
    avg_cpc = total_spend / total_clicks if total_clicks else 0
    avg_cvr = total_conv / total_clicks if total_clicks else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Spend", f"${total_spend:,.2f}")
    k2.metric("Total Conversions", f"{total_conv:,}")
    k3.metric("Avg CPA", f"${avg_cpa:,.2f}")
    k4.metric("Avg CTR", f"{avg_ctr:.2%}")

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Impressions", f"{total_imp:,}")
    k6.metric("Clicks", f"{total_clicks:,}")
    k7.metric("Avg CPC", f"${avg_cpc:,.2f}")
    k8.metric("Conv Rate", f"{avg_cvr:.2%}")

    st.divider()

    # Daily Spend Trend
    st.subheader("Daily Spend by Platform")
    fig = px.line(
        daily_f,
        x="date",
        y="total_spend",
        color="platform",
        color_discrete_map=COLORS,
        labels={"total_spend": "Spend ($)", "date": ""},
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, title=None),
        hovermode="x unified",
        margin=dict(t=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Donut + Conversions bar
    plat_agg = fdf.groupby("platform", as_index=False).agg(
        total_spend=("spend", "sum"), total_conversions=("conversions", "sum")
    )

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Spend Distribution")
        fig = px.pie(
            plat_agg,
            values="total_spend",
            names="platform",
            color="platform",
            color_discrete_map=COLORS,
            hole=0.5,
        )
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Conversions by Platform")
        fig = px.bar(
            plat_agg.sort_values("total_conversions"),
            x="total_conversions",
            y="platform",
            color="platform",
            color_discrete_map=COLORS,
            orientation="h",
            text_auto=True,
            labels={"total_conversions": "Conversions", "platform": ""},
        )
        fig.update_layout(showlegend=False, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    # Daily Conversions
    st.subheader("Daily Conversions by Platform")
    fig = px.line(
        daily_f,
        x="date",
        y="total_conversions",
        color="platform",
        color_discrete_map=COLORS,
        labels={"total_conversions": "Conversions", "date": ""},
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, title=None),
        hovermode="x unified",
        margin=dict(t=10),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── TAB 2: PLATFORM DEEP DIVE ─────────────────────────────────────────────────
with tab2:
    st.subheader("Platform Comparison")
    if not plat_f.empty:
        disp = plat_f[
            [
                "platform",
                "campaigns",
                "total_impressions",
                "total_clicks",
                "total_spend",
                "total_conversions",
                "avg_ctr",
                "avg_cpc",
                "avg_cpa",
                "avg_conversion_rate",
                "avg_cpm",
                "spend_share",
                "conversion_share",
            ]
        ].copy()
        disp.columns = [
            "Platform",
            "Campaigns",
            "Impressions",
            "Clicks",
            "Spend ($)",
            "Conversions",
            "CTR",
            "CPC ($)",
            "CPA ($)",
            "Conv Rate",
            "CPM ($)",
            "Spend Share",
            "Conv Share",
        ]
        st.dataframe(
            disp.style.format(
                {
                    "Impressions": "{:,.0f}",
                    "Clicks": "{:,.0f}",
                    "Spend ($)": "${:,.2f}",
                    "Conversions": "{:,.0f}",
                    "CTR": "{:.2%}",
                    "CPC ($)": "${:,.2f}",
                    "CPA ($)": "${:,.2f}",
                    "Conv Rate": "{:.2%}",
                    "CPM ($)": "${:,.2f}",
                    "Spend Share": "{:.1%}",
                    "Conv Share": "{:.1%}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # Radar chart
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Efficiency Radar")
        if not plat_f.empty:
            metrics = []
            for _, r in plat_f.iterrows():
                ctr_v = float(r["avg_ctr"]) if pd.notna(r["avg_ctr"]) else 0
                cvr_v = (
                    float(r["avg_conversion_rate"])
                    if pd.notna(r["avg_conversion_rate"])
                    else 0
                )
                cpa_v = (
                    1 / float(r["avg_cpa"])
                    if pd.notna(r["avg_cpa"]) and float(r["avg_cpa"]) > 0
                    else 0
                )
                cpc_v = (
                    1 / float(r["avg_cpc"])
                    if pd.notna(r["avg_cpc"]) and float(r["avg_cpc"]) > 0
                    else 0
                )
                metrics.append(
                    {
                        "platform": r["platform"],
                        "CTR": ctr_v,
                        "Conv Rate": cvr_v,
                        "Cost Eff (1/CPA)": cpa_v,
                        "Click Eff (1/CPC)": cpc_v,
                    }
                )
            mdf = pd.DataFrame(metrics)
            cats = ["CTR", "Conv Rate", "Cost Eff (1/CPA)", "Click Eff (1/CPC)"]
            for c in cats:
                mx = mdf[c].max()
                if mx > 0:
                    mdf[c] = mdf[c] / mx
            fig = go.Figure()
            for _, r in mdf.iterrows():
                fig.add_trace(
                    go.Scatterpolar(
                        r=[r[c] for c in cats] + [r[cats[0]]],
                        theta=cats + [cats[0]],
                        fill="toself",
                        name=r["platform"],
                        line_color=COLORS.get(r["platform"], "#888"),
                        opacity=0.7,
                    )
                )
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1.05])),
                legend=dict(orientation="h", y=-0.15, title=None),
                margin=dict(t=30, b=30),
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("CPA Trend Over Time")
        fig = px.line(
            daily_f,
            x="date",
            y="avg_cpa",
            color="platform",
            color_discrete_map=COLORS,
            labels={"avg_cpa": "CPA ($)", "date": ""},
        )
        fig.update_layout(
            legend=dict(orientation="h", y=-0.15, title=None),
            hovermode="x unified",
            margin=dict(t=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    # CPM + Weekly
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("CPM by Platform")
        if not plat_f.empty:
            fig = px.bar(
                plat_f.sort_values("avg_cpm"),
                x="avg_cpm",
                y="platform",
                color="platform",
                color_discrete_map=COLORS,
                orientation="h",
                text_auto="$.2f",
                labels={"avg_cpm": "CPM ($)", "platform": ""},
            )
            fig.update_layout(showlegend=False, margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Weekly Spend")
        if not weekly_f.empty:
            fig = px.bar(
                weekly_f,
                x="week_start",
                y="spend",
                color="platform",
                color_discrete_map=COLORS,
                barmode="group",
                labels={"spend": "Spend ($)", "week_start": "Week"},
            )
            fig.update_layout(
                legend=dict(orientation="h", y=-0.15, title=None), margin=dict(t=10)
            )
            fig.update_xaxes(tickformat="%b %d")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # TikTok funnel
    if "TikTok" in platforms and not tt_funnel.empty:
        st.subheader("TikTok: Video Completion Funnel")
        totals = tt_funnel[
            [
                "total_views",
                "watched_25pct",
                "watched_50pct",
                "watched_75pct",
                "watched_100pct",
            ]
        ].sum()
        stages = pd.DataFrame(
            {
                "Stage": [
                    "Views",
                    "25% Watched",
                    "50% Watched",
                    "75% Watched",
                    "100% Watched",
                ],
                "Count": [
                    totals["total_views"],
                    totals["watched_25pct"],
                    totals["watched_50pct"],
                    totals["watched_75pct"],
                    totals["watched_100pct"],
                ],
            }
        )
        stages["Pct"] = stages["Count"] / stages["Count"].iloc[0] * 100
        fig = px.funnel(
            stages,
            x="Count",
            y="Stage",
            text=[
                f"{int(c):,} ({p:.0f}%)"
                for c, p in zip(stages["Count"], stages["Pct"])
            ],
        )
        fig.update_traces(
            marker_color=["#000", "#333", "#555", "#777", "#999"]
        )
        st.plotly_chart(fig, use_container_width=True)

    # Google quality
    if "Google" in platforms and not gq.empty:
        st.subheader("Google: Quality Score vs CPA")
        fig = px.scatter(
            gq,
            x="avg_quality_score",
            y="avg_cpa",
            size="total_cost",
            color="campaign_name",
            hover_name="ad_group_name",
            labels={"avg_quality_score": "Quality Score", "avg_cpa": "CPA ($)"},
        )
        fig.update_layout(
            legend=dict(orientation="h", y=-0.2, title=None), margin=dict(t=10)
        )
        st.plotly_chart(fig, use_container_width=True)


# ── TAB 3: CAMPAIGN ANALYSIS ──────────────────────────────────────────────────
with tab3:
    st.subheader("Campaign Performance Ranking")
    if not camp_f.empty:
        disp = camp_f[
            [
                "platform",
                "campaign_name",
                "total_spend",
                "total_impressions",
                "total_clicks",
                "total_conversions",
                "avg_ctr",
                "avg_cpc",
                "avg_cpa",
                "avg_conversion_rate",
                "spend_rank",
                "cpa_rank",
            ]
        ].copy()
        disp.columns = [
            "Platform",
            "Campaign",
            "Spend ($)",
            "Impressions",
            "Clicks",
            "Conversions",
            "CTR",
            "CPC ($)",
            "CPA ($)",
            "Conv Rate",
            "Spend Rank",
            "CPA Rank",
        ]
        st.dataframe(
            disp.style.format(
                {
                    "Spend ($)": "${:,.2f}",
                    "Impressions": "{:,.0f}",
                    "Clicks": "{:,.0f}",
                    "Conversions": "{:,.0f}",
                    "CTR": "{:.2%}",
                    "CPC ($)": "${:,.2f}",
                    "CPA ($)": "${:,.2f}",
                    "Conv Rate": "{:.2%}",
                    "Spend Rank": "{:.0f}",
                    "CPA Rank": "{:.0f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("CPA by Campaign (lower is better)")
            fig = px.bar(
                camp_f.sort_values("avg_cpa"),
                y="campaign_name",
                x="avg_cpa",
                color="platform",
                color_discrete_map=COLORS,
                orientation="h",
                text_auto="$.2f",
                labels={"avg_cpa": "CPA ($)", "campaign_name": ""},
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                legend=dict(orientation="h", y=-0.15, title=None),
                margin=dict(t=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("CTR vs Conversion Rate")
            fig = px.scatter(
                camp_f,
                x="avg_ctr",
                y="avg_conversion_rate",
                color="platform",
                size="total_spend",
                color_discrete_map=COLORS,
                hover_name="campaign_name",
                labels={"avg_ctr": "CTR", "avg_conversion_rate": "Conv Rate"},
            )
            fig.update_xaxes(tickformat=".1%")
            fig.update_yaxes(tickformat=".1%")
            fig.update_layout(
                legend=dict(orientation="h", y=-0.15, title=None), margin=dict(t=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Spend vs Conversions (Efficiency Frontier)")
        st.markdown("Campaigns closer to **top-left** = more efficient.")
        fig = px.scatter(
            camp_f,
            x="total_spend",
            y="total_conversions",
            color="platform",
            color_discrete_map=COLORS,
            hover_name="campaign_name",
            size="total_clicks",
            labels={
                "total_spend": "Total Spend ($)",
                "total_conversions": "Conversions",
            },
        )
        fig.update_xaxes(tickprefix="$", tickformat=",")
        fig.update_layout(
            legend=dict(orientation="h", y=-0.15, title=None), margin=dict(t=10)
        )
        st.plotly_chart(fig, use_container_width=True)


# ── TAB 4: INSIGHTS ───────────────────────────────────────────────────────────
with tab4:
    st.subheader("Key Findings")

    if not plat_f.empty:
        best_cpa_row = plat_f.loc[plat_f["avg_cpa"].astype(float).idxmin()]
        worst_cpa_row = plat_f.loc[plat_f["avg_cpa"].astype(float).idxmax()]
        best_ctr_row = plat_f.loc[plat_f["avg_ctr"].astype(float).idxmax()]
        most_imp_row = plat_f.loc[
            plat_f["total_impressions"].astype(int).idxmax()
        ]

        gap = float(worst_cpa_row["avg_cpa"]) - float(best_cpa_row["avg_cpa"])
        with st.expander(
            f"**[Efficiency]** {best_cpa_row['platform']} delivers lowest CPA at ${float(best_cpa_row['avg_cpa']):,.2f}",
            expanded=True,
        ):
            st.markdown(
                f"{best_cpa_row['platform']} CPA is ${gap:,.2f} lower than "
                f"{worst_cpa_row['platform']} (${float(worst_cpa_row['avg_cpa']):,.2f}). "
                f"Consider shifting budget toward {best_cpa_row['platform']} for cost-efficient conversions."
            )

        for _, r in plat_f.iterrows():
            ss = float(r.get("spend_share", 0))
            cs = float(r.get("conversion_share", 0))
            if ss > 0 and cs > 0:
                ratio = cs / ss
                if ratio < 0.8:
                    with st.expander(
                        f"**[Budget]** {r['platform']} gets {ss:.0%} spend but only {cs:.0%} conversions"
                    ):
                        st.markdown(
                            f"{(ss - cs):.1%} gap between budget and conversions for "
                            f"{r['platform']}. Evaluate if justified by upper-funnel goals."
                        )
                elif ratio > 1.2:
                    with st.expander(
                        f"**[Budget]** {r['platform']} over-delivers: {cs:.0%} conversions on {ss:.0%} spend"
                    ):
                        st.markdown(
                            f"{r['platform']} converts efficiently. "
                            f"Strong candidate for budget increase."
                        )

        with st.expander(
            f"**[Engagement]** {best_ctr_row['platform']} has highest CTR at {float(best_ctr_row['avg_ctr']):.2%}"
        ):
            st.markdown(
                f"High CTR = strong ad-audience relevance. "
                f"CPC: ${float(best_ctr_row['avg_cpc']):,.2f}, "
                f"Conv Rate: {float(best_ctr_row['avg_conversion_rate']):.2%}."
            )

        with st.expander(
            f"**[Reach]** {most_imp_row['platform']} drives most impressions ({int(most_imp_row['total_impressions']):,})"
        ):
            st.markdown(
                f"CPM: ${float(most_imp_row['avg_cpm']):,.2f}. Best suited for awareness campaigns."
            )

    if not camp_f.empty:
        best_c = camp_f.loc[camp_f["avg_cpa"].astype(float).idxmin()]
        worst_c = camp_f.loc[camp_f["avg_cpa"].astype(float).idxmax()]
        with st.expander(
            f"**[Campaign]** Best: {best_c['campaign_name']} ({best_c['platform']}) "
            f"-- CPA ${float(best_c['avg_cpa']):,.2f}",
            expanded=True,
        ):
            st.markdown(
                f"{int(best_c['total_conversions']):,} conversions on "
                f"${float(best_c['total_spend']):,.2f} spend. Scale this campaign."
            )
        with st.expander(
            f"**[Campaign]** Highest CPA: {worst_c['campaign_name']} ({worst_c['platform']}) "
            f"-- ${float(worst_c['avg_cpa']):,.2f}"
        ):
            st.markdown(
                f"{float(worst_c['avg_cpa']) / float(best_c['avg_cpa']):.1f}x higher than best. "
                f"Review targeting and creative."
            )

    st.divider()
    st.subheader("Recommendations")
    if not plat_f.empty:
        best = plat_f.loc[plat_f["avg_cpa"].astype(float).idxmin()]
        worst = plat_f.loc[plat_f["avg_cpa"].astype(float).idxmax()]
        ts = float(plat_f["total_spend"].sum())
        bs = float(best["total_spend"]) / ts if ts else 0
        st.markdown(
            f"- **Increase {best['platform']} budget** (currently {bs:.0%}): "
            f"lowest CPA at ${float(best['avg_cpa']):,.2f}. Shift 10-20% from {worst['platform']}."
        )
    if not camp_f.empty:
        top = camp_f.nsmallest(1, "avg_cpa").iloc[0]
        bot = camp_f.nlargest(1, "avg_cpa").iloc[0]
        st.markdown(
            f"- **Scale** {top['campaign_name']} ({top['platform']}): "
            f"${float(top['avg_cpa']):,.2f} CPA."
        )
        st.markdown(
            f"- **Optimize/pause** {bot['campaign_name']} ({bot['platform']}): "
            f"${float(bot['avg_cpa']):,.2f} CPA."
        )
    if not plat_f.empty and len(plat_f) == 3:
        st.markdown(
            "- **Maintain 3-platform diversification**: TikTok/Facebook for awareness, "
            "Google for high-intent conversions."
        )

    st.divider()
    st.subheader("Methodology")
    st.markdown(
        """
| Metric | Formula | Use |
|--------|---------|-----|
| **CTR** | Clicks / Impressions | Ad relevance |
| **CPC** | Spend / Clicks | Click cost |
| **CPA** | Spend / Conversions | Acquisition cost |
| **Conv Rate** | Conversions / Clicks | Funnel efficiency |
| **CPM** | Spend / Impressions x 1000 | Reach cost |
| **ROAS** | Revenue / Spend | Return (Google only) |

Data: Facebook, Google, TikTok ads unified via Snowflake SQL.
"""
    )
