-- Per business + customer: the raw Recency / Frequency / Monetary inputs for the
-- RFM segmentation mart.
--   * Recency   -> days from the customer's last receipt to the latest receipt
--                  in the whole dataset (smaller = more recently active).
--   * Frequency -> number of receipts.
--   * Monetary  -> total net-of-discount revenue.
-- Anonymous receipts (no customer name) are excluded — a customer must be
-- identifiable to be segmented.
with sales as (
    select
        business_name,
        customer_name,
        receipt_ref,
        receipt_date,
        net_revenue
    from {{ ref('int_business_fiscal_sales') }}
    where customer_name is not null
),

as_of as (
    -- Reference "today" for recency: the most recent receipt in the dataset.
    select max(receipt_date) as as_of_date from sales
),

per_customer as (
    select
        business_name,
        customer_name,
        max(receipt_date)           as last_purchase_date,
        count(receipt_ref)          as frequency,
        round(sum(net_revenue), 2)  as monetary
    from sales
    group by business_name, customer_name
)

select
    c.business_name,
    c.customer_name,
    c.last_purchase_date,
    date_diff('day', c.last_purchase_date, a.as_of_date) as recency_days,
    c.frequency,
    c.monetary
from per_customer c
cross join as_of a
