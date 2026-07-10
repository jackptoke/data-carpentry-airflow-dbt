-- Q1 mart: monthly profit and sales count per business.
-- (Formerly q1/business_monthly_profits.sql.)
with sales as (
    select * from {{ ref('int_business_sales_profits') }}
)

select
    business_abn,
    business_name,
    year,
    month,
    month_name,
    sum(total_profit)   as total_monthly_profit,
    count(receipt_ref)  as num_of_sales
from sales
group by business_abn, business_name, year, month, month_name
order by business_name, year, month
