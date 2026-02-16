"""
charts.py — Plotly chart factory functions for the Improvado dashboard.

Each function returns a Plotly figure object ready for st.plotly_chart().
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PLATFORM_COLORS = {"Facebook": "#1877F2", "Google": "#34A853", "TikTok": "#000000"}


# ─────────────────────────────────────────────────────────────────────────────
# Executive Overview Charts
# ─────────────────────────────────────────────────────────────────────────────

def daily_spend_trend(daily: pd.DataFrame) :
    """Line chart: daily spend per platform."""
    fig = px.line(
        daily,
        x="date",
        y="total_spend",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        labels={"total_spend": "Daily Spend ($)", "date": ""},
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, title=None),
        hovermode="x unified",
        margin=dict(t=10, l=0, r=0),
    )
    fig.update_traces(hovertemplate="%{y:$,.0f}")
    return fig


def spend_share_donut(plat: pd.DataFrame) :
    """Donut chart: spend distribution across platforms."""
    fig = px.pie(
        plat,
        values="total_spend",
        names="platform",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        hole=0.5,
    )
    fig.update_traces(textinfo="percent+label", textposition="outside")
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
    return fig


def conversions_by_platform(plat: pd.DataFrame) :
    """Bar chart: total conversions per platform."""
    fig = px.bar(
        plat.sort_values("total_conversions", ascending=True),
        x="total_conversions",
        y="platform",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        orientation="h",
        text_auto=True,
        labels={"total_conversions": "Conversions", "platform": ""},
    )
    fig.update_layout(showlegend=False, margin=dict(t=10, l=0, r=0))
    return fig


def daily_conversions_trend(daily: pd.DataFrame) :
    """Line chart: daily conversions per platform."""
    fig = px.line(
        daily,
        x="date",
        y="total_conversions",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        labels={"total_conversions": "Daily Conversions", "date": ""},
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, title=None),
        hovermode="x unified",
        margin=dict(t=10, l=0, r=0),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Platform Deep-Dive Charts
# ─────────────────────────────────────────────────────────────────────────────

def cpa_trend_by_platform(daily: pd.DataFrame) :
    """Line chart: CPA over time per platform."""
    fig = px.line(
        daily,
        x="date",
        y="avg_cpa",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        labels={"avg_cpa": "CPA ($)", "date": ""},
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, title=None),
        hovermode="x unified",
        margin=dict(t=10, l=0, r=0),
    )
    fig.update_traces(hovertemplate="%{y:$,.2f}")
    return fig


def cpm_comparison(plat: pd.DataFrame) :
    """Bar chart: CPM comparison across platforms."""
    fig = px.bar(
        plat.sort_values("avg_cpm", ascending=True),
        x="avg_cpm",
        y="platform",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        orientation="h",
        text_auto="$.2f",
        labels={"avg_cpm": "CPM ($)", "platform": ""},
    )
    fig.update_layout(showlegend=False, margin=dict(t=10, l=0, r=0))
    return fig


def platform_kpi_radar(plat: pd.DataFrame) :
    """Radar chart: normalized KPIs per platform (CTR, Conv Rate, 1/CPA, 1/CPC)."""
    metrics = []
    for _, row in plat.iterrows():
        metrics.append({
            "platform": row["platform"],
            "CTR": float(row["avg_ctr"]) if row["avg_ctr"] else 0,
            "Conv Rate": float(row["avg_conversion_rate"]) if row["avg_conversion_rate"] else 0,
            "Cost Efficiency (1/CPA)": 1 / float(row["avg_cpa"]) if row["avg_cpa"] and float(row["avg_cpa"]) > 0 else 0,
            "Click Efficiency (1/CPC)": 1 / float(row["avg_cpc"]) if row["avg_cpc"] and float(row["avg_cpc"]) > 0 else 0,
        })

    mdf = pd.DataFrame(metrics)
    # Normalize each metric column to 0-1 range for radar chart
    for col in ["CTR", "Conv Rate", "Cost Efficiency (1/CPA)", "Click Efficiency (1/CPC)"]:
        max_val = mdf[col].max()
        if max_val > 0:
            mdf[col] = mdf[col] / max_val

    categories = ["CTR", "Conv Rate", "Cost Efficiency (1/CPA)", "Click Efficiency (1/CPC)"]

    fig = go.Figure()
    for _, row in mdf.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row[c] for c in categories] + [row[categories[0]]],
            theta=categories + [categories[0]],
            fill="toself",
            name=row["platform"],
            line_color=PLATFORM_COLORS.get(row["platform"], "#888"),
            opacity=0.7,
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1.05])),
        legend=dict(orientation="h", y=-0.15, title=None),
        margin=dict(t=30, b=30),
    )
    return fig


def tiktok_funnel_chart(funnel_df: pd.DataFrame) :
    """Funnel chart: TikTok video watch completion stages."""
    totals = funnel_df[["total_views", "watched_25pct", "watched_50pct",
                        "watched_75pct", "watched_100pct"]].sum()
    stages = pd.DataFrame({
        "Stage": ["Video Views", "25% Watched", "50% Watched", "75% Watched", "100% Watched"],
        "Count": [totals["total_views"], totals["watched_25pct"], totals["watched_50pct"],
                  totals["watched_75pct"], totals["watched_100pct"]],
    })
    # Calculate drop-off percentages
    stages["Pct of Views"] = stages["Count"] / stages["Count"].iloc[0] * 100

    fig = px.funnel(
        stages,
        x="Count",
        y="Stage",
        text=[f"{int(c):,} ({p:.0f}%)" for c, p in zip(stages["Count"], stages["Pct of Views"])],
    )
    fig.update_traces(marker_color=["#000000", "#333333", "#555555", "#777777", "#999999"])
    fig.update_layout(margin=dict(t=10, b=10))
    return fig


def google_quality_chart(gq_df: pd.DataFrame) :
    """Scatter: quality score vs CPA for Google ad groups."""
    fig = px.scatter(
        gq_df,
        x="avg_quality_score",
        y="avg_cpa",
        size="total_cost",
        color="campaign_name",
        hover_name="ad_group_name",
        labels={
            "avg_quality_score": "Avg Quality Score",
            "avg_cpa": "CPA ($)",
            "total_cost": "Total Cost",
        },
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.2, title=None),
        margin=dict(t=10),
    )
    fig.update_traces(hovertemplate="QS: %{x}<br>CPA: $%{y:,.2f}<br>%{customdata}")
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Campaign Analysis Charts
# ─────────────────────────────────────────────────────────────────────────────

def cpa_by_campaign(camp: pd.DataFrame) :
    """Horizontal bar: CPA per campaign (lower = better)."""
    camp_sorted = camp.sort_values("avg_cpa", ascending=True)
    fig = px.bar(
        camp_sorted,
        y="campaign_name",
        x="avg_cpa",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        orientation="h",
        text_auto="$.2f",
        labels={"avg_cpa": "CPA ($)", "campaign_name": ""},
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        legend=dict(orientation="h", y=-0.15, title=None),
        margin=dict(t=10, l=0, r=0),
    )
    return fig


def ctr_vs_conversion_rate(camp: pd.DataFrame) :
    """Scatter: CTR vs conversion rate, sized by spend."""
    fig = px.scatter(
        camp,
        x="avg_ctr",
        y="avg_conversion_rate",
        color="platform",
        size="total_spend",
        color_discrete_map=PLATFORM_COLORS,
        hover_name="campaign_name",
        labels={"avg_ctr": "CTR", "avg_conversion_rate": "Conversion Rate"},
    )
    fig.update_xaxes(tickformat=".1%")
    fig.update_yaxes(tickformat=".1%")
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, title=None),
        margin=dict(t=10),
    )
    return fig


def spend_vs_conversions(camp: pd.DataFrame) :
    """Scatter: total spend vs total conversions per campaign."""
    fig = px.scatter(
        camp,
        x="total_spend",
        y="total_conversions",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        hover_name="campaign_name",
        size="total_clicks",
        labels={"total_spend": "Total Spend ($)", "total_conversions": "Conversions"},
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, title=None),
        margin=dict(t=10),
    )
    fig.update_xaxes(tickprefix="$", tickformat=",")
    return fig


def weekly_spend_heatmap(weekly: pd.DataFrame) :
    """Grouped bar: weekly spend by platform."""
    fig = px.bar(
        weekly,
        x="week_start",
        y="spend",
        color="platform",
        color_discrete_map=PLATFORM_COLORS,
        barmode="group",
        labels={"spend": "Spend ($)", "week_start": "Week", "platform": "Platform"},
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, title=None),
        margin=dict(t=10, b=10),
    )
    fig.update_xaxes(tickformat="%b %d")
    return fig
