-- One row per receipt: the business that issued it.
with source as (
    select * from {{ source('raw', 'raw_receipts') }}
)
select
    Reference      as receipt_ref,
    Business.ABN   as business_abn,
    Business.Name  as business_name
from source
