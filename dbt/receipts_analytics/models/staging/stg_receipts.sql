-- Receipt header: one row per receipt.
-- Date is parsed to a real DATE here so downstream models never re-cast it.
with source as (
    select * from {{ source('raw', 'raw_receipts') }}
)
select
    Reference                                 as receipt_ref,
    Sequence                                  as sequence_num,
    cast(strptime(Date, '%Y/%m/%d') as date)  as receipt_date,
    GST                                       as gst,
    Terminal                                  as terminal_num,
    Total                                     as receipt_total
from source
