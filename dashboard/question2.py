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


def show_lollipop_graph(
    df,
    header: str,
    value_col: Literal["amount_spent", "num_purchases"],
):
    """Render a 2x2 grid of lollipop charts of the top customers per business."""
    fig = make_subplots(
        rows=2, cols=2, subplot_titles=BUSINESSES, vertical_spacing=0.2
    )
    for i, business in enumerate(BUSINESSES):
        row, col = divmod(i, 2)
        business_df = df[df["business_name"] == business]
        colour = BUSINESS_COLOURS[business]
        names = business_df["customer_name"]
        values = business_df[value_col]

        # Stems: a line from the baseline (0) up to each value, with a None
        # break between customers so the segments don't connect to each other.
        stem_x, stem_y = [], []
        for name, value in zip(names, values):
            stem_x += [name, name, None]
            stem_y += [0, value, None]
        fig.add_trace(
            go.Scatter(
                x=stem_x,
                y=stem_y,
                mode="lines",
                line=dict(color=colour, width=2),
                hoverinfo="skip",
                showlegend=False,
            ),
            row=row + 1,
            col=col + 1,
        )

        # Heads: the dot at each value, with the value labelled above it.
        fig.add_trace(
            go.Scatter(
                x=names,
                y=values,
                mode="markers+text",
                marker=dict(size=13, color=colour, line=dict(color="white", width=1)),
                text=values,
                texttemplate="%{text:.2s}",
                textposition="top center",
                name=business,
                hovertemplate="%{x}<br>%{y}<extra></extra>",
                showlegend=False,
            ),
            row=row + 1,
            col=col + 1,
        )

        # Start each axis at 0 and leave headroom so the value labels aren't clipped.
        if len(values):
            fig.update_yaxes(
                range=[0, float(values.max()) * 1.18], row=row + 1, col=col + 1
            )
    fig.update_layout(title_text=header, height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


st.markdown("#### Top 10 Customers by Amount Spent")
by_spend = run_query("SELECT * FROM main.fct_top_customers_by_spend")
st.dataframe(by_spend)
show_lollipop_graph(by_spend, "Top 10 Customers by Amount Spent", value_col="amount_spent")

st.markdown("#### Top 10 Customers by Number of Purchases")
by_purchases = run_query("SELECT * FROM main.fct_top_customers_by_purchases")
st.dataframe(by_purchases)
show_lollipop_graph(
    by_purchases, "Top 10 Customers by Number of Purchases", value_col="num_purchases"
)
