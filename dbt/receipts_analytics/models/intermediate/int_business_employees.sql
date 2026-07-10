-- Distinct (business, month, cashier) observations — an employee is "active"
-- in a month if they processed at least one receipt for that business.
-- (Formerly q3/business_employees.sql.)
with businesses as (
    select * from {{ ref('stg_businesses') }}
),

cashiers as (
    select * from {{ ref('stg_cashiers') }}
),

receipts as (
    select * from {{ ref('stg_receipts') }}
)

select distinct
    b.business_name,
    extract(year  from r.receipt_date)  as year,
    extract(month from r.receipt_date)  as month,
    strftime(r.receipt_date, '%B')      as month_name,
    c.cashier_name
from businesses b
join cashiers c on b.receipt_ref = c.receipt_ref
join receipts r on r.receipt_ref = b.receipt_ref
