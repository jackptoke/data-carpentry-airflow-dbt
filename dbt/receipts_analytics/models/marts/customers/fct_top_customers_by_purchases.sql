-- Q2 mart: top 10 customers per business by number of purchases.
-- (Formerly q2/top_ten_customers_by_num_purchases.sql.)
with summary as (
    select * from {{ ref('int_customer_business_summary') }}
),

ranked as (
    select
        business_name,
        customer_name,
        num_purchases,
        round(amount_spent, 2) as amount_spent,
        row_number() over (
            partition by business_name
            order by num_purchases desc, amount_spent desc
        ) as ranking
    from summary
)

select *
from ranked
where ranking <= 10
order by business_name, ranking
