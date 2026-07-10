-- One row per payment line: the Payments list is unnested to the row grain.
-- (Replaces the former pandas Python model with native DuckDB list unnesting.)
with source as (
    select Reference, Payments
    from {{ source('raw', 'raw_receipts') }}
    where length(Payments) > 0
),
unnested as (
    select
        Reference          as receipt_ref,
        unnest(Payments)   as payment
    from source
)
select
    receipt_ref,
    payment.Method  as payment_method,
    payment.Amount  as payment_amount
from unnested
