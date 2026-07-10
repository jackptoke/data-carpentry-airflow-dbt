-- One row per promotion line: the Promotions list is unnested to the row grain.
-- (Replaces the former pandas Python model with native DuckDB list unnesting.)
with source as (
    select Reference, Promotions
    from {{ source('raw', 'raw_receipts') }}
    where length(Promotions) > 0
),
unnested as (
    select
        Reference            as receipt_ref,
        unnest(Promotions)   as promotion
    from source
)
select
    receipt_ref,
    promotion.Product       as product_name,
    promotion.Discount      as discount,
    promotion.Per_Quantity  as per_quantity
from unnested
