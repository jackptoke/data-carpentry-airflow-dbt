from typing import Literal

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from constants import BUSINESS_COLOURS, BUSINESSES, run_query

st.markdown("## Q2 - Which customers were most loyal for each business?")
st.markdown(
    "We treat a *loyal customer* two ways: someone who spends the most, and "
    "someone who makes the most purchases. Both views are shown below."
)


def show_bar_graph(
    df,
    header: str,
    value_col: Literal["amount_spent", "num_purchases"],
):
    """Render a 2x2 grid of the top customers per business for one metric."""
    fig = make_subplots(
        rows=2, cols=2, subplot_titles=BUSINESSES, vertical_spacing=0.2
    )
    for i, business in enumerate(BUSINESSES):
        row, col = divmod(i, 2)
        business_df = df[df["business_name"] == business]
        fig.add_trace(
            go.Bar(
                x=business_df["customer_name"],
                y=business_df[value_col],
                text=business_df[value_col],
                textposition="outside",
                texttemplate="%{text:.2s}",
                name=business,
                marker=dict(cornerradius=30, color=BUSINESS_COLOURS[business]),
            ),
            row=row + 1,
            col=col + 1,
        )
    fig.update_layout(title_text=header, height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


st.markdown("#### Top 10 Customers by Amount Spent")
by_spend = run_query("SELECT * FROM main.fct_top_customers_by_spend")
st.dataframe(by_spend)
show_bar_graph(by_spend, "Top 10 Customers by Amount Spent", value_col="amount_spent")

st.markdown("#### Top 10 Customers by Number of Purchases")
by_purchases = run_query("SELECT * FROM main.fct_top_customers_by_purchases")
st.dataframe(by_purchases)
show_bar_graph(
    by_purchases, "Top 10 Customers by Number of Purchases", value_col="num_purchases"
)
