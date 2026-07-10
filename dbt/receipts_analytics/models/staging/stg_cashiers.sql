-- One row per receipt: the cashier (employee) who processed it.
select
    Reference  as receipt_ref,
    Cashier    as cashier_name
from {{ source('raw', 'raw_receipts') }}
