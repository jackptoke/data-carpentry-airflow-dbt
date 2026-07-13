-- Finance KPI (semantic) layer: headline metrics per business per fiscal year
-- (July–June), with year-on-year deltas. This is the single mart the executive
-- dashboard reads. It gives an analyst the numbers they would actually report:
--   * net_revenue / gross_profit / gross_margin_pct  — profitability
--   * num_transactions / num_customers               — scale and reach
--   * avg_order_value / purchases_per_customer        — behaviour
--   * revenue_yoy_pct / profit_yoy_pct                — momentum (window lag)
with fiscal_sales as (
    select * from {{ ref('int_business_fiscal_sales') }}
),

aggregated as (
    select
        business_abn,
        business_name,
        fiscal_year,
        fiscal_year || '-' || (fiscal_year + 1)  as fiscal_year_label,
        round(sum(net_revenue), 2)               as net_revenue,
        round(sum(cogs), 2)                       as cogs,
        round(sum(gross_profit), 2)               as gross_profit,
        count(receipt_ref)                        as num_transactions,
        count(distinct customer_name)             as num_customers
    from fiscal_sales
    group by business_abn, business_name, fiscal_year
),

with_ratios as (
    select
        *,
        round(gross_profit * 100.0 / nullif(net_revenue, 0), 2)      as gross_margin_pct,
        round(net_revenue / nullif(num_transactions, 0), 2)          as avg_order_value,
        round(num_transactions * 1.0 / nullif(num_customers, 0), 2)  as purchases_per_customer
    from aggregated
),

with_prior as (
    select
        *,
        lag(net_revenue)  over (partition by business_abn order by fiscal_year)  as prev_net_revenue,
        lag(gross_profit) over (partition by business_abn order by fiscal_year)  as prev_gross_profit
    from with_ratios
)

select
    business_abn,
    business_name,
    fiscal_year,
    fiscal_year_label,
    net_revenue,
    cogs,
    gross_profit,
    gross_margin_pct,
    num_transactions,
    num_customers,
    avg_order_value,
    purchases_per_customer,
    round((net_revenue  - prev_net_revenue)  * 100.0 / nullif(prev_net_revenue, 0), 2)   as revenue_yoy_pct,
    round((gross_profit - prev_gross_profit) * 100.0 / nullif(prev_gross_profit, 0), 2)  as profit_yoy_pct
from with_prior
order by business_name, fiscal_year
