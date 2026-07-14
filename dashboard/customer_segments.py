import plotly.express as px
import streamlit as st

from constants import run_query

# A distinct, stable colour per segment, ordered roughly best → worst.
SEGMENT_COLOURS = {
    "Champions": "#2ca02c",
    "Loyal": "#1f77b4",
    "Potential Loyalist": "#17becf",
    "New Customer": "#9467bd",
    "Needs Attention": "#ff7f0e",
    "At Risk": "#d62728",
    "Cannot Lose Them": "#e377c2",
    "Hibernating": "#7f7f7f",
    "Others": "#bcbd22",
}
SEGMENT_ACTION = {
    "Champions": "Reward, upsell, ask for referrals",
    "Loyal": "Keep engaged; introduce new products",
    "Potential Loyalist": "Nurture into loyal with offers",
    "New Customer": "Onboard and encourage a second visit",
    "Needs Attention": "Re-activate before they lapse",
    "At Risk": "Win-back campaign — they were valuable",
    "Cannot Lose Them": "Urgent re-engagement — high value, gone quiet",
    "Hibernating": "Low-cost reactivation",
    "Others": "Monitor",
}

st.markdown("# 👥 Customer Segments (RFM)")
st.markdown(
    "**RFM** scores every customer on three behaviours — **R**ecency (days since "
    "their last purchase), **F**requency (number of purchases) and **M**onetary "
    "(total spend). Each is ranked into 1–5 quintiles *within its business* "
    "(`fct_customer_rfm`), and the Recency×Frequency grid maps to a named, "
    "action-oriented segment. It turns raw receipts into *who to act on, and how*."
)
st.caption(
    "Caveat: each business has only ~12–29 named customers, so the quintiles are "
    "coarse — the segments illustrate the method rather than a fine-grained split."
)

rfm = run_query("SELECT * FROM main.fct_customer_rfm")

businesses = ["All businesses"] + sorted(rfm["business_name"].unique())
choice = st.selectbox("Business", businesses)
df = rfm if choice == "All businesses" else rfm[rfm["business_name"] == choice]

# --- Segment summary ----------------------------------------------------------
summary = (
    df.groupby("segment")
    .agg(
        customers=("customer_name", "count"),
        total_value=("monetary", "sum"),
        avg_recency_days=("recency_days", "mean"),
    )
    .reset_index()
    .sort_values("total_value", ascending=False)
)
summary["action"] = summary["segment"].map(SEGMENT_ACTION)

c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("### Value by segment")
    tm = px.treemap(
        summary,
        path=["segment"],
        values="total_value",
        color="segment",
        color_discrete_map=SEGMENT_COLOURS,
    )
    tm.update_traces(textinfo="label+value")
    tm.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=380, showlegend=False)
    st.plotly_chart(tm, use_container_width=True)
with c2:
    st.markdown("### Recommended action")
    st.dataframe(
        summary[["segment", "customers", "total_value", "action"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "total_value": st.column_config.NumberColumn("value", format="$%.0f"),
        },
    )

# --- RFM scatter (the classic view) ------------------------------------------
st.markdown("### The RFM grid")
st.caption(
    "Each dot is a customer — position by Recency (x, lower = more recent) and "
    "Frequency (y), sized by Monetary value, coloured by segment."
)
sc = px.scatter(
    df,
    x="recency_days",
    y="frequency",
    size="monetary",
    color="segment",
    color_discrete_map=SEGMENT_COLOURS,
    hover_name="customer_name",
    hover_data={"monetary": ":.0f", "recency_days": True, "frequency": True},
    size_max=40,
)
sc.update_layout(
    xaxis_title="Recency (days since last purchase — lower = more recent)",
    yaxis_title="Frequency (purchases)",
    legend_title="Segment",
    height=520,
)
st.plotly_chart(sc, use_container_width=True)

# --- Insights -----------------------------------------------------------------
total_value = df["monetary"].sum()
champ = df[df["segment"] == "Champions"]
winback = df[df["segment"].isin(["At Risk", "Cannot Lose Them"])]
st.markdown("### Key insights")
st.markdown(
    f"- **Champions drive disproportionate value** — {len(champ)} customers "
    f"({len(champ) / max(len(df), 1) * 100:.0f}% of the base) account for "
    f"${champ['monetary'].sum():,.0f} ({champ['monetary'].sum() / max(total_value, 1) * 100:.0f}% of value). "
    "Protect and reward them.\n"
    f"- **Re-engagement opportunity** — {len(winback)} *At Risk* / *Cannot Lose "
    f"Them* customers, together worth ${winback['monetary'].sum():,.0f}, were "
    "valuable but have gone quiet. A targeted win-back is the highest-ROI action.\n"
    "- **The segment mix is the story** — a healthy base grows Champions/Loyal and "
    "shrinks Hibernating over time; tracking this quarter-on-quarter is the metric "
    "a retention team would own."
)
