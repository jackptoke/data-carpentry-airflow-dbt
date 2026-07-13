"""Executive summary — the headline view of the receipts analytics platform.

Reads the KPI (semantic) layer `fct_business_kpis`: one row per business per
fiscal year with revenue, gross margin, transactions, AOV and year-on-year
deltas. The page opens on the latest complete fiscal year, shows portfolio
totals with YoY movement, then breaks the numbers down by business.
"""
import plotly.graph_objects as go
import streamlit as st

from constants import BUSINESS_COLOURS, run_query

st.markdown("# 📊 Executive Summary")
st.caption(
    "A portfolio view of four small businesses — revenue, profitability and "
    "customer behaviour — served read-only from the DuckDB marts built by the "
    "Airflow + dbt pipeline."
)

kpis = run_query(
    "SELECT * FROM main.fct_business_kpis ORDER BY business_name, fiscal_year"
)

# The dashboard headlines the most recent complete fiscal year and compares it
# with the one before, so the numbers stay correct as new data lands.
latest_fy = int(kpis["fiscal_year"].max())
prior_fy = latest_fy - 1
latest_label = kpis.loc[kpis["fiscal_year"] == latest_fy, "fiscal_year_label"].iloc[0]

latest = kpis[kpis["fiscal_year"] == latest_fy]
prior = kpis[kpis["fiscal_year"] == prior_fy]


def _pct_delta(current: float, previous: float) -> str | None:
    """YoY change as a '+x.x% YoY' string for st.metric (None if no prior year)."""
    if not previous:
        return None
    return f"{(current - previous) / previous * 100:+.1f}% YoY"


rev_now, rev_prev = latest["net_revenue"].sum(), prior["net_revenue"].sum()
profit_now, profit_prev = latest["gross_profit"].sum(), prior["gross_profit"].sum()
txns_now, txns_prev = latest["num_transactions"].sum(), prior["num_transactions"].sum()
margin_now = profit_now / rev_now * 100 if rev_now else 0
margin_prev = profit_prev / rev_prev * 100 if rev_prev else 0

st.markdown(f"### Portfolio performance — FY {latest_label}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Net Revenue", f"${rev_now:,.0f}", _pct_delta(rev_now, rev_prev))
c2.metric("Gross Profit", f"${profit_now:,.0f}", _pct_delta(profit_now, profit_prev))
c3.metric(
    "Gross Margin",
    f"{margin_now:.1f}%",
    f"{margin_now - margin_prev:+.1f} pts" if margin_prev else None,
)
c4.metric("Transactions", f"{txns_now:,.0f}", _pct_delta(txns_now, txns_prev))

st.caption(
    "Deltas compare the latest complete fiscal year (July–June) with the one "
    "before. Revenue and profit are net of promotional discounts."
)

# --- Revenue trend by business -------------------------------------------------
st.markdown("### Net revenue by business")
rev_fig = go.Figure()
for business in kpis["business_name"].unique():
    data = kpis[kpis["business_name"] == business]
    rev_fig.add_trace(
        go.Scatter(
            x=data["fiscal_year_label"],
            y=data["net_revenue"],
            mode="lines+markers",
            name=business,
            line=dict(color=BUSINESS_COLOURS.get(business), width=3),
        )
    )
rev_fig.update_layout(
    xaxis_title="Fiscal year",
    yaxis_title="Net revenue ($)",
    legend_title="Business",
    hovermode="x unified",
)
st.plotly_chart(rev_fig, use_container_width=True)

# --- Latest-year scorecard -----------------------------------------------------
st.markdown(f"### FY {latest_label} scorecard")
scorecard = (
    latest[
        [
            "business_name",
            "net_revenue",
            "gross_margin_pct",
            "num_transactions",
            "num_customers",
            "avg_order_value",
            "revenue_yoy_pct",
            "profit_yoy_pct",
        ]
    ]
    .sort_values("net_revenue", ascending=False)
    .rename(
        columns={
            "business_name": "Business",
            "net_revenue": "Net revenue",
            "gross_margin_pct": "Gross margin",
            "num_transactions": "Transactions",
            "num_customers": "Customers",
            "avg_order_value": "AOV",
            "revenue_yoy_pct": "Revenue YoY",
            "profit_yoy_pct": "Profit YoY",
        }
    )
)
st.dataframe(
    scorecard,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Net revenue": st.column_config.NumberColumn(format="$%.0f"),
        "Gross margin": st.column_config.NumberColumn(format="%.1f%%"),
        "AOV": st.column_config.NumberColumn(format="$%.2f"),
        "Revenue YoY": st.column_config.NumberColumn(format="%+.1f%%"),
        "Profit YoY": st.column_config.NumberColumn(format="%+.1f%%"),
    },
)

# --- Margin trend --------------------------------------------------------------
st.markdown("### Gross margin trend")
margin_fig = go.Figure()
for business in kpis["business_name"].unique():
    data = kpis[kpis["business_name"] == business]
    margin_fig.add_trace(
        go.Scatter(
            x=data["fiscal_year_label"],
            y=data["gross_margin_pct"],
            mode="lines+markers",
            name=business,
            line=dict(color=BUSINESS_COLOURS.get(business), width=3),
        )
    )
margin_fig.update_layout(
    xaxis_title="Fiscal year",
    yaxis_title="Gross margin (%)",
    legend_title="Business",
    hovermode="x unified",
)
st.plotly_chart(margin_fig, use_container_width=True)

# --- Insights ------------------------------------------------------------------
st.markdown("### Key insights")
st.markdown(
    f"- **Pizza Pronto is the growth engine.** It compounds revenue every year "
    f"and overtook Penguin Swim School to become the #2 business by FY {latest_label}, "
    "on the back of steadily rising transaction volume and a climbing margin.\n"
    "- **Margins are healthy and improving** — the portfolio runs a ~50–53% blended "
    "gross margin, trending up as the businesses mature.\n"
    f"- **Watch basket size in FY {latest_label}.** Transaction counts hit a record, "
    "yet revenue and average order value fell for three of the four businesses — "
    "customers are buying *more often but smaller*. That divergence between volume "
    "and value is the number to interrogate next quarter.\n"
    "- **Ed's Barber Supplies carries the portfolio** on revenue and the highest AOV, "
    "but its growth has flattened after the FY2024-25 step-change."
)
