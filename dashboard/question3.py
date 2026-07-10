import plotly.graph_objects as go
import streamlit as st

from constants import BUSINESS_COLOURS, run_query

st.markdown("## Q3 - What is the employee turnover rate of each business?")
st.markdown(
    "Turnover is computed entirely in dbt (`fct_employee_turnover`), so it is "
    "reproducible rather than hand-counted. An **employee** is a cashier "
    "observed on receipts; they are **active** in a July–June fiscal year if "
    "they processed at least one receipt that year, and counted as a "
    "**departure** in their last active year. "
    "`turnover_rate_pct = num_left / headcount * 100`."
)
st.info(
    "**Right-censoring:** the most recent fiscal year is flagged "
    "`is_censored_period`. Every still-employed person's last active year is "
    "that final year, so they would all look like departures. Turnover is left "
    "out for that year instead of producing a spurious spike — the exact "
    "artefact an earlier, manual version of this analysis ran into."
)

turnover = run_query("SELECT * FROM main.fct_employee_turnover")
attendance = run_query("SELECT * FROM main.dim_employee_attendance")

# ---- Interactive filter -----------------------------------------------------
selected = st.multiselect(
    "Businesses to show",
    options=list(BUSINESS_COLOURS),
    default=list(BUSINESS_COLOURS),
)
turnover = turnover[turnover["business_name"].isin(selected)]

st.markdown("### Turnover by fiscal year")
st.dataframe(turnover, use_container_width=True)

# ---- Turnover trend (excludes the censored final year) ----------------------
trend = turnover[~turnover["is_censored_period"]]
fig = go.Figure()
for business in selected:
    data = trend[trend["business_name"] == business].sort_values("fiscal_year")
    fig.add_trace(
        go.Scatter(
            x=data["fiscal_year_label"],
            y=data["turnover_rate_pct"],
            mode="lines+markers",
            name=business,
            line=dict(color=BUSINESS_COLOURS.get(business)),
        )
    )
fig.update_layout(
    title="Employee Turnover Rate by Fiscal Year (censored final year excluded)",
    xaxis_title="Fiscal Year",
    yaxis_title="Turnover Rate (%)",
    legend_title="Businesses",
)
st.plotly_chart(fig, use_container_width=True)

# ---- Headline: average / median turnover per business -----------------------
st.markdown("### Average and median turnover (excluding the censored year)")
summary = (
    trend.groupby("business_name")["turnover_rate_pct"]
    .agg(avg_turnover_rate="mean", median_turnover_rate="median")
    .round(2)
    .reset_index()
)
summary = summary[summary["business_name"].isin(selected)]
st.dataframe(summary, use_container_width=True)

summary_fig = go.Figure(
    data=[
        go.Bar(
            name="Avg. Turnover Rate",
            x=summary["business_name"],
            y=summary["avg_turnover_rate"],
            text=summary["avg_turnover_rate"],
            marker=dict(color="#fb5607"),
        ),
        go.Bar(
            name="Median Turnover Rate",
            x=summary["business_name"],
            y=summary["median_turnover_rate"],
            text=summary["median_turnover_rate"],
            marker=dict(color="#ff006e"),
        ),
    ]
)
summary_fig.update_layout(barmode="group", yaxis_title="Turnover Rate (%)")
st.plotly_chart(summary_fig, use_container_width=True)

st.markdown(
    "Employee turnover is a crucial measure of workforce stability. These are "
    "very small businesses (1–5 staff at a time), so losing even one or two "
    "people a year produces a high turnover rate. Excluding the censored final "
    "year, turnover sits in a believable range for micro-businesses, and the "
    "misleading end-of-data spike is handled explicitly rather than explained "
    "away."
)

# ---- Supporting roster ------------------------------------------------------
with st.expander("Monthly employee roster (dim_employee_attendance)"):
    roster = attendance[attendance["business_name"].isin(selected)]
    st.dataframe(roster, use_container_width=True)
