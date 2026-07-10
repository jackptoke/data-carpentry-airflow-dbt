-- One row per product line: the Products list is unnested to the row grain.
-- (Replaces the former pandas Python model with native DuckDB list unnesting.)
with source as (
    select Reference, Products
    from {{ source('raw', 'raw_receipts') }}
    where length(Products) > 0
),
unnested as (
    select
        Reference          as receipt_ref,
        unnest(Products)   as product
    from source
)
select
    receipt_ref,
    product.Name      as product_name,
    product.Cost      as product_cost,
    product.Price     as product_price,
    product.Quantity  as product_quantity
from unnested
