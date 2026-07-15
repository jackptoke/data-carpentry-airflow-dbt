import plotly.express as px
import streamlit as st

from constants import BUSINESS_COLOURS, run_query

st.markdown("# 📦 Product Performance & Margin")
st.markdown(
    "Revenue alone is misleading — a high-selling product on a thin margin can "
    "earn less than a quieter, richer one. This view pairs each product's revenue "
    "with its **gross margin** and **profit** (`fct_product_performance`), so the "
    "*volume traps* and the *quiet earners* both stand out. Discounts are netted "
    "off using the same promotion logic as the profit models."
)

perf = run_query("SELECT * FROM main.fct_product_performance")

businesses = ["All businesses"] + sorted(perf["business_name"].unique())
choice = st.selectbox("Business", businesses)
df = perf if choice == "All businesses" else perf[perf["business_name"] == choice]

# --- Margin map ---------------------------------------------------------------
st.markdown("### Margin map — revenue vs. margin")
st.caption(
    "Each bubble is a product: revenue on the x-axis, gross margin on the y-axis, "
    "bubble size = total gross profit. Top-right = high revenue *and* rich margin "
    "(stars); bottom-right = big sellers on thin margins (volume traps)."
)
mm = px.scatter(
    df,
    x="net_revenue",
    y="gross_margin_pct",
    size="gross_profit",
    color="business_name",
    color_discrete_map=BUSINESS_COLOURS,
    hover_name="product_name",
    hover_data={"units_sold": True, "gross_profit": ":.0f", "business_name": False},
    size_max=45,
)
mm.update_layout(
    xaxis_title="Net revenue ($)",
    yaxis_title="Gross margin (%)",
    legend_title="Business",
    height=520,
)
st.plotly_chart(mm, use_container_width=True)

# --- Revenue vs profit for the top products -----------------------------------
st.markdown("### Revenue ≠ profit")
st.caption("Top products by revenue, with gross profit alongside — the gap is margin.")
top = df.sort_values("net_revenue", ascending=False).head(12)
long = top.melt(
    id_vars="product_name",
    value_vars=["net_revenue", "gross_profit"],
    var_name="metric",
    value_name="value",
)
bar = px.bar(
    long,
    x="value",
    y="product_name",
    color="metric",
    barmode="group",
    orientation="h",
    color_discrete_map={"net_revenue": "#8338ec", "gross_profit": "#2ca02c"},
    labels={"metric": "", "value": "$", "product_name": ""},
)
bar.update_layout(
    yaxis=dict(categoryorder="total ascending"),
    legend=dict(orientation="h", y=1.02),
    height=520,
)
st.plotly_chart(bar, use_container_width=True)

# --- Table --------------------------------------------------------------------
st.markdown("### Product detail")
table = df.sort_values("gross_profit", ascending=False)[
    ["business_name", "product_name", "units_sold", "net_revenue", "gross_profit",
     "gross_margin_pct", "discount_given", "revenue_rank", "profit_rank"]
]
st.dataframe(
    table,
    hide_index=True,
    use_container_width=True,
    column_config={
        "net_revenue": st.column_config.NumberColumn("net revenue", format="$%.0f"),
        "gross_profit": st.column_config.NumberColumn("gross profit", format="$%.0f"),
        "gross_margin_pct": st.column_config.NumberColumn("margin", format="%.1f%%"),
        "discount_given": st.column_config.NumberColumn("discount given", format="$%.0f"),
    },
)

# --- Insights -----------------------------------------------------------------
st.markdown("### Key insights")
# Volume trap: biggest positive (profit_rank - revenue_rank) gap.
scope = df.copy()
scope["rank_gap"] = scope["profit_rank"] - scope["revenue_rank"]
trap = scope.sort_values("rank_gap", ascending=False).iloc[0]
star = scope.sort_values("rank_gap").iloc[0]
richest = df.loc[df["gross_margin_pct"].idxmax()]
total_discount = df["discount_given"].sum()
st.markdown(
    f"- **Volume trap** — *{trap['product_name']}* ({trap['business_name']}) ranks "
    f"#{int(trap['revenue_rank'])} on revenue but only #{int(trap['profit_rank'])} on "
    f"profit ({trap['gross_margin_pct']:.0f}% margin): it sells well but earns less "
    "than its revenue suggests.\n"
    f"- **Quiet earner** — *{star['product_name']}* ({star['business_name']}) "
    f"punches above its revenue rank (#{int(star['revenue_rank'])} → "
    f"#{int(star['profit_rank'])} on profit) on a healthier margin.\n"
    f"- **Richest margin** — *{richest['product_name']}* at "
    f"{richest['gross_margin_pct']:.0f}%.\n"
    f"- **Discounts given up** — ${total_discount:,.0f} of revenue conceded to "
    "promotions across these products — worth checking against the volume they drove."
)
