-- One row per (receipt) linking a customer to a business and the amount spent.
-- (Replaces the pandas q2/business_customers.py model with pure SQL.)
with receipts as (
    select * from {{ ref('stg_receipts') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

businesses as (
    select * from {{ ref('stg_businesses') }}
)

select
    r.receipt_ref,
    c.customer_name,
    b.business_name,
    r.receipt_total as amount_spent
from receipts r
join customers  c on r.receipt_ref = c.receipt_ref
join businesses b on r.receipt_ref = b.receipt_ref
where c.customer_name is not null
  and b.business_name is not null
  and r.receipt_total > 0
