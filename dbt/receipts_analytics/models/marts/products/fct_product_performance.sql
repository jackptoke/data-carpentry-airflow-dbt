-- Product-performance mart: one row per (business, product) with revenue, cost,
-- profit, gross margin %, the discount given up, and the product's rank within
-- its business by both revenue and profit. The revenue vs profit rank gap is the
-- headline — high-revenue products are not always the most profitable.
with perf as (
    select * from {{ ref('int_product_sales') }}
)

select
    business_abn,
    business_name,
    product_name,
    units_sold,
    gross_revenue,
    net_revenue,
    cost,
    gross_profit,
    round(gross_profit * 100.0 / nullif(net_revenue, 0), 1)  as gross_margin_pct,
    round(gross_revenue - net_revenue, 2)                    as discount_given,
    row_number() over (
        partition by business_name order by net_revenue desc
    )                                                        as revenue_rank,
    row_number() over (
        partition by business_name order by gross_profit desc
    )                                                        as profit_rank
from perf
order by business_name, gross_profit desc
