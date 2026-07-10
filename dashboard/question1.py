import plotly.graph_objects as go
import streamlit as st

from constants import BUSINESS_COLOURS, run_query

st.markdown("### Questions")
st.markdown("1. Are there periods of the year where some businesses are more profitable?")
st.markdown("2. Which customers were most loyal for each business?")
st.markdown("3. What is the employee turnover rate of each business?")

st.markdown("### Raw Data")
st.caption("`main.raw_receipts` — one row per receipt, loaded from JSON with nested structs/lists.")
st.dataframe(run_query("SELECT * FROM main.raw_receipts"))

st.markdown("#### Strategy")
st.markdown(
    "1. The nested raw receipts are normalised into staging models (`stg_*`).\n"
    "2. Business logic is layered in intermediate views (`int_*`) and published "
    "as marts (`fct_*` / `dim_*`).\n"
    "3. The marts are visualised below to answer each question."
)

st.markdown("#### Normalised (staging) tables")
st.markdown("##### stg_receipts")
st.dataframe(run_query("SELECT * FROM main.stg_receipts"))
other_staging = [
    "stg_businesses",
    "stg_cashiers",
    "stg_customers",
    "stg_payments",
    "stg_products",
    "stg_promotions",
]
for left, right in zip(other_staging[0::2], other_staging[1::2]):
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(f"##### {left}")
        st.dataframe(run_query(f"SELECT * FROM main.{left}"))
    with col_r:
        st.markdown(f"##### {right}")
        st.dataframe(run_query(f"SELECT * FROM main.{right}"))

st.markdown("## Q1. Are there periods of the year where some businesses are more profitable?")
st.markdown("### 1. Sales by business (`int_business_sales`)")
st.dataframe(run_query("SELECT * FROM main.int_business_sales"))
st.markdown("### 2. Profit per receipt (`int_receipt_profits`)")
st.dataframe(run_query("SELECT * FROM main.int_receipt_profits"))
st.markdown("### 3. Business sales and profits (`int_business_sales_profits`)")
st.dataframe(run_query("SELECT * FROM main.int_business_sales_profits"))

st.markdown("### 4. Monthly profits per business (`fct_business_monthly_profits`)")
monthly = run_query("SELECT * FROM main.fct_business_monthly_profits")
monthly["month_year"] = monthly["month"].astype(str) + "-" + monthly["year"].astype(str)
st.dataframe(monthly)

fig = go.Figure()
for business in monthly["business_name"].unique():
    data = monthly[monthly["business_name"] == business]
    fig.add_trace(
        go.Scatter(
            x=data["month_year"],
            y=data["total_monthly_profit"],
            mode="lines+markers",
            name=business,
            line=dict(color=BUSINESS_COLOURS.get(business)),
        )
    )
fig.update_layout(
    title="Monthly Profits Across Businesses",
    xaxis_title="Month",
    yaxis_title="Total Profit ($)",
    xaxis_tickangle=270,
    legend_title="Businesses",
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("#### Observations")
st.markdown(
    "1. **Ed's Barber Supplies** grows year on year and performs especially well "
    "in the first five months of the year.\n"
    "2. **Please Bring Pizza Pronto** performs strongly across the year, roughly "
    "doubling its profit every two years.\n"
    "3. **Penguin Swim School** dips in the middle of the year (Australian "
    "winter) and grows only sporadically.\n"
    "4. **Wake Up with Coffee** grows less than Ed's or Pizza Pronto, but is more "
    "stable than Penguin Swim School."
)
