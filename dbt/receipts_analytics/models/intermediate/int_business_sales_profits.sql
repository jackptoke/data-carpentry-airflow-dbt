-- One row per receipt: business + calendar context joined to receipt profit.
-- (Formerly q1/business_sales_profits.sql.)
with sales as (
    select * from {{ ref('int_business_sales') }}
),

profits as (
    select * from {{ ref('int_receipt_profits') }}
)

select
    s.business_abn,
    s.business_name,
    s.receipt_date,
    s.year,
    s.month,
    s.month_name,
    s.receipt_ref,
    s.receipt_total,
    s.gst,
    p.total_cost,
    p.total_price,
    p.total_price_after_discount,
    p.total_profit
from sales s
join profits p on s.receipt_ref = p.receipt_ref
