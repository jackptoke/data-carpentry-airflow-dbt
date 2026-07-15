-- Per business + product: units, revenue, cost and profit — the inputs to the
-- product-performance mart. Discounts use the same qualifying-quantity logic as
-- int_receipt_profits (a line's price is discounted when at least one whole
-- multiple of the promotion's per_quantity is bought), so product profit
-- reconciles with the receipt/KPI profit basis.
with products as (
    select
        p.receipt_ref,
        p.product_name,
        p.product_quantity,
        p.product_cost  * p.product_quantity  as line_cost,
        p.product_price * p.product_quantity   as line_gross
    from {{ ref('stg_products') }} p
),

businesses as (
    select receipt_ref, business_abn, business_name
    from {{ ref('stg_businesses') }}
),

promotions as (
    select receipt_ref, product_name, discount, per_quantity
    from {{ ref('stg_promotions') }}
),

lines as (
    select
        b.business_abn,
        b.business_name,
        p.product_name,
        p.product_quantity,
        p.line_cost,
        p.line_gross,
        case
            when d.discount is not null
                 and floor(p.product_quantity / d.per_quantity) * d.per_quantity > 0
                then p.line_gross * (1.0 - d.discount)
            else p.line_gross
        end as line_net
    from products p
    join businesses b on p.receipt_ref = b.receipt_ref
    left join promotions d
        on  p.receipt_ref  = d.receipt_ref
        and p.product_name = d.product_name
)

select
    business_abn,
    business_name,
    product_name,
    sum(product_quantity)          as units_sold,
    round(sum(line_gross), 2)      as gross_revenue,
    round(sum(line_net), 2)        as net_revenue,
    round(sum(line_cost), 2)       as cost,
    round(sum(line_net - line_cost), 2) as gross_profit
from lines
group by business_abn, business_name, product_name
