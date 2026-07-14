-- Customer mart: RFM segmentation. Scores each customer 1–5 on Recency,
-- Frequency and Monetary within their business (NTILE quintiles), then maps the
-- Recency×Frequency grid to a named, action-oriented segment.
--
-- SMALL-SAMPLE CAVEAT: each business has only ~12–29 named customers, so the
-- quintiles are coarse (2–6 customers per bucket) and NTILE breaks ties by row
-- order rather than value. The segmentation demonstrates the method; on a
-- dataset this small the segments are illustrative rather than statistically
-- fine-grained. Monetary is scored but kept off the segment axes (a classic
-- R×F grid) and surfaced separately as the value dimension.
with rfm as (
    select * from {{ ref('int_customer_rfm') }}
),

scored as (
    select
        business_name,
        customer_name,
        last_purchase_date,
        recency_days,
        frequency,
        monetary,
        -- Recent purchase => high R. Order by recency descending so the
        -- least-recently-active customers fall into bucket 1.
        ntile(5) over (partition by business_name order by recency_days desc) as r_score,
        ntile(5) over (partition by business_name order by frequency asc)     as f_score,
        ntile(5) over (partition by business_name order by monetary asc)      as m_score
    from rfm
)

select
    business_name,
    customer_name,
    last_purchase_date,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    case
        when r_score >= 4 and f_score >= 4 then 'Champions'
        when r_score <= 2 and f_score >= 4 then 'Cannot Lose Them'
        when f_score >= 4                  then 'Loyal'
        when r_score <= 2 and f_score >= 3 then 'At Risk'
        when r_score >= 4 and f_score >= 2 then 'Potential Loyalist'
        when r_score >= 4                  then 'New Customer'
        when r_score = 3                   then 'Needs Attention'
        when r_score <= 2 and f_score <= 2 then 'Hibernating'
        else 'Others'
    end as segment
from scored
order by business_name, monetary desc
