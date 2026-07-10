-- Receipts enriched with the issuing business and calendar parts.
-- (Formerly q1/business_sales.sql; date parts now derive from the DATE in staging.)
with receipts as (
    select * from {{ ref('stg_receipts') }}
),

businesses as (
    select * from {{ ref('stg_businesses') }}
)

select
    b.business_abn,
    b.business_name,
    r.receipt_ref,
    r.receipt_date,
    r.receipt_total,
    r.gst,
    extract(year  from r.receipt_date)  as year,
    extract(month from r.receipt_date)  as month,
    strftime(r.receipt_date, '%B')      as month_name
from receipts r
join businesses b on r.receipt_ref = b.receipt_ref
