-- Profit per receipt, after applying any qualifying promotions.
-- (Formerly q1/sale_profits.sql, which referenced receipt_promotions without ref().)
with products as (
    select
        receipt_ref,
        product_name,
        product_quantity,
        product_cost  * product_quantity  as total_cost,
        product_price * product_quantity  as total_price
    from {{ ref('stg_products') }}
),

promotions as (
    select receipt_ref, product_name, discount, per_quantity
    from {{ ref('stg_promotions') }}
),

lines_with_discount as (
    select
        p.receipt_ref,
        p.total_cost,
        p.total_price,
        d.discount,
        -- units that qualify for the promotion (whole multiples of per_quantity)
        floor(p.product_quantity / d.per_quantity) * d.per_quantity as discount_qualifying_qty
    from products p
    left join promotions d
        on  p.receipt_ref  = d.receipt_ref
        and p.product_name = d.product_name
),

line_profits as (
    select
        receipt_ref,
        total_cost,
        total_price,
        case
            when discount is not null and discount_qualifying_qty > 0
                then total_price * (1.0 - discount)
            else total_price
        end as price_after_discount
    from lines_with_discount
)

select
    receipt_ref,
    round(sum(total_cost), 2)                         as total_cost,
    round(sum(total_price), 2)                        as total_price,
    round(sum(price_after_discount), 2)               as total_price_after_discount,
    round(sum(price_after_discount - total_cost), 2)  as total_profit
from line_profits
group by receipt_ref
