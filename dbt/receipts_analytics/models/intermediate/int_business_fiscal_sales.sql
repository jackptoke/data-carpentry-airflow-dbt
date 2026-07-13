-- One row per receipt, enriched with the fiscal year (July–June, matching the
-- turnover model) and the customer named on it. Carries the net-of-discount
-- revenue and profit basis that the KPI mart rolls up.
with sales_profits as (
    select * from {{ ref('int_business_sales_profits') }}
),

customers as (
    select receipt_ref, customer_name from {{ ref('stg_customers') }}
)

select
    s.business_abn,
    s.business_name,
    s.receipt_ref,
    s.receipt_date,
    case when s.month >= 7 then s.year else s.year - 1 end  as fiscal_year,
    c.customer_name,
    s.total_price_after_discount  as net_revenue,
    s.total_cost                  as cogs,
    s.total_profit                as gross_profit
from sales_profits s
left join customers c on s.receipt_ref = c.receipt_ref
