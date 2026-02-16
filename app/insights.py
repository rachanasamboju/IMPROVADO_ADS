"""
insights.py — Automated insight generation for the Improvado dashboard.

Analyzes the data and returns structured insight strings
to surface in the dashboard's Insights tab.
"""

import pandas as pd


def generate_executive_insights(
    plat_summary: pd.DataFrame,
    camp_perf: pd.DataFrame,
    weekly: pd.DataFrame,
) :
    """
    Generate a list of insight dictionaries with keys:
      - category: str  (e.g. "Efficiency", "Budget", "Trend")
      - title: str
      - detail: str
      - severity: str  ("positive", "neutral", "warning")
    """
    insights = []

    # ── 1. Lowest CPA platform ──
    best_cpa = plat_summary.loc[plat_summary["avg_cpa"].idxmin()]
    worst_cpa = plat_summary.loc[plat_summary["avg_cpa"].idxmax()]
    cpa_gap = float(worst_cpa["avg_cpa"]) - float(best_cpa["avg_cpa"])
    insights.append({
        "category": "Efficiency",
        "title": f"{best_cpa['platform']} delivers the lowest CPA at ${float(best_cpa['avg_cpa']):,.2f}",
        "detail": (
            f"{best_cpa['platform']} achieves a CPA of ${float(best_cpa['avg_cpa']):,.2f}, "
            f"which is ${cpa_gap:,.2f} lower than {worst_cpa['platform']} "
            f"(${float(worst_cpa['avg_cpa']):,.2f}). Consider shifting budget toward "
            f"{best_cpa['platform']} if the goal is cost-efficient conversions."
        ),
        "severity": "positive",
    })

    # ── 2. Spend vs conversion share mismatch ──
    for _, row in plat_summary.iterrows():
        spend_share = float(row.get("spend_share", 0))
        conv_share = float(row.get("conversion_share", 0))
        if spend_share > 0 and conv_share > 0:
            ratio = conv_share / spend_share
            if ratio < 0.8:
                insights.append({
                    "category": "Budget",
                    "title": f"{row['platform']} receives {spend_share:.0%} of spend but only {conv_share:.0%} of conversions",
                    "detail": (
                        f"There is a {(spend_share - conv_share):.1%} gap between budget allocation "
                        f"and conversion output for {row['platform']}. This suggests the platform may be "
                        f"over-funded relative to its conversion efficiency. Evaluate whether this spend "
                        f"is justified by upper-funnel objectives (brand awareness, reach)."
                    ),
                    "severity": "warning",
                })
            elif ratio > 1.2:
                insights.append({
                    "category": "Budget",
                    "title": f"{row['platform']} over-delivers: {conv_share:.0%} of conversions on {spend_share:.0%} of spend",
                    "detail": (
                        f"{row['platform']} is converting efficiently — producing a disproportionately "
                        f"high share of conversions relative to its budget. This is a strong candidate "
                        f"for budget increase to capture more volume at efficient rates."
                    ),
                    "severity": "positive",
                })

    # ── 3. Best and worst campaigns ──
    if not camp_perf.empty:
        best_camp = camp_perf.loc[camp_perf["avg_cpa"].idxmin()]
        worst_camp = camp_perf.loc[camp_perf["avg_cpa"].idxmax()]
        insights.append({
            "category": "Campaign",
            "title": f"Best campaign: {best_camp['campaign_name']} ({best_camp['platform']})",
            "detail": (
                f"CPA of ${float(best_camp['avg_cpa']):,.2f} with "
                f"{int(best_camp['total_conversions']):,} conversions on "
                f"${float(best_camp['total_spend']):,.2f} spend. "
                f"CTR: {float(best_camp['avg_ctr']):.2%}, "
                f"Conv Rate: {float(best_camp['avg_conversion_rate']):.2%}."
            ),
            "severity": "positive",
        })
        insights.append({
            "category": "Campaign",
            "title": f"Highest CPA campaign: {worst_camp['campaign_name']} ({worst_camp['platform']})",
            "detail": (
                f"CPA of ${float(worst_camp['avg_cpa']):,.2f} — "
                f"{float(worst_camp['avg_cpa']) / float(best_camp['avg_cpa']):.1f}x higher than the best. "
                f"Total spend: ${float(worst_camp['total_spend']):,.2f}, "
                f"conversions: {int(worst_camp['total_conversions']):,}. "
                f"Review targeting, creative, and bid strategy for optimization."
            ),
            "severity": "warning",
        })

    # ── 4. CTR leader ──
    best_ctr = plat_summary.loc[plat_summary["avg_ctr"].idxmax()]
    insights.append({
        "category": "Engagement",
        "title": f"{best_ctr['platform']} has the highest CTR at {float(best_ctr['avg_ctr']):.2%}",
        "detail": (
            f"High CTR indicates strong ad-audience relevance. "
            f"Combined with a CPC of ${float(best_ctr['avg_cpc']):,.2f} and "
            f"conversion rate of {float(best_ctr['avg_conversion_rate']):.2%}, "
            f"this platform shows strong top-of-funnel engagement."
        ),
        "severity": "positive",
    })

    # ── 5. Volume leader ──
    most_impressions = plat_summary.loc[plat_summary["total_impressions"].idxmax()]
    insights.append({
        "category": "Reach",
        "title": f"{most_impressions['platform']} drives the most impressions ({int(most_impressions['total_impressions']):,})",
        "detail": (
            f"With {int(most_impressions['total_impressions']):,} impressions and "
            f"a CPM of ${float(most_impressions['avg_cpm']):,.2f}, "
            f"{most_impressions['platform']} is the primary reach driver. "
            f"This makes it well-suited for awareness and consideration campaigns."
        ),
        "severity": "neutral",
    })

    # ── 6. Weekly trend analysis ──
    if not weekly.empty:
        latest_week = weekly[weekly["week_start"] == weekly["week_start"].max()]
        for _, row in latest_week.iterrows():
            wow = row.get("spend_wow_change")
            if wow is not None and pd.notna(wow):
                wow_float = float(wow)
                direction = "increased" if wow_float > 0 else "decreased"
                insights.append({
                    "category": "Trend",
                    "title": f"{row['platform']} spend {direction} {abs(wow_float):.1%} week-over-week",
                    "detail": (
                        f"Latest week spend for {row['platform']}: ${float(row['spend']):,.2f}. "
                        f"Conversions WoW change: {float(row.get('conversions_wow_change', 0)):.1%}. "
                        f"Monitor whether spend changes are proportional to conversion changes."
                    ),
                    "severity": "neutral" if abs(wow_float) < 0.15 else "warning",
                })

    return insights


def generate_budget_recommendations(
    plat_summary: pd.DataFrame,
    camp_perf: pd.DataFrame,
) :
    """Generate actionable budget allocation recommendations."""
    recs = []

    if plat_summary.empty:
        return recs

    # Find the most efficient platform
    best = plat_summary.loc[plat_summary["avg_cpa"].idxmin()]
    worst = plat_summary.loc[plat_summary["avg_cpa"].idxmax()]

    total_spend = float(plat_summary["total_spend"].sum())
    best_spend = float(best["total_spend"])
    best_share = best_spend / total_spend if total_spend > 0 else 0

    recs.append(
        f"**Increase {best['platform']} budget share** (currently {best_share:.0%}): "
        f"It has the lowest CPA (${float(best['avg_cpa']):,.2f}) and the highest conversion efficiency. "
        f"A 10-20% budget shift from {worst['platform']} could yield more conversions at lower cost."
    )

    # Campaign-level recommendations
    if not camp_perf.empty and len(camp_perf) > 1:
        top_camp = camp_perf.nsmallest(1, "avg_cpa").iloc[0]
        bottom_camp = camp_perf.nlargest(1, "avg_cpa").iloc[0]
        recs.append(
            f"**Scale top performer:** {top_camp['campaign_name']} ({top_camp['platform']}) "
            f"at ${float(top_camp['avg_cpa']):,.2f} CPA is the best-performing campaign. "
            f"Increase its daily budget or expand its audience targeting."
        )
        recs.append(
            f"**Optimize or pause:** {bottom_camp['campaign_name']} ({bottom_camp['platform']}) "
            f"has a CPA of ${float(bottom_camp['avg_cpa']):,.2f}. "
            f"Test new creatives, tighten targeting, or reallocate its budget."
        )

    # Cross-platform diversification
    if len(plat_summary) == 3:
        recs.append(
            "**Maintain cross-platform diversification:** Running on 3 platforms reduces "
            "audience saturation risk. Each platform serves different funnel stages — "
            "use TikTok/Facebook for awareness, Google for high-intent conversion capture."
        )

    return recs
