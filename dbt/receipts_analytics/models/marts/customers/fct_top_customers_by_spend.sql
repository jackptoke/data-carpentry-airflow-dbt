-- Q2 mart: top 10 customers per business by total amount spent.
-- (Formerly q2/top_ten_customers_by_business_value.sql.)
with summary as (
    select * from {{ ref('int_customer_business_summary') }}
),

ranked as (
    select
        business_name,
        customer_name,
        round(amount_spent, 2) as amount_spent,
        num_purchases,
        row_number() over (
            partition by business_name
            order by amount_spent desc, num_purchases desc
        ) as ranking
    from summary
)

select *
from ranked
where ranking <= 10
order by business_name, ranking
