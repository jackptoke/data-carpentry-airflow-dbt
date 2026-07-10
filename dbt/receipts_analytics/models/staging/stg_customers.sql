-- One row per receipt: the customer named on it (may be null for anonymous sales).
with source as (
    select * from {{ source('raw', 'raw_receipts') }}
)
select
    Reference              as receipt_ref,
    Customer.Name          as customer_name,
    Customer.Points_Earnt  as customer_points
from source
