-- Per business + customer: total spend and number of purchases.
-- (Formerly q2/business_customers_summary.sql.)
with spend as (
    select * from {{ ref('int_customer_business_spend') }}
)

select
    business_name,
    customer_name,
    sum(amount_spent)   as amount_spent,
    count(receipt_ref)  as num_purchases
from spend
group by business_name, customer_name
