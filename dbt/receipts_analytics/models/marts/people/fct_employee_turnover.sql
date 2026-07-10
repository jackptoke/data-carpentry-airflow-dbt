-- Q3 mart: employee turnover per business per fiscal year (July–June).
--
-- Replaces the earlier manual, hand-counted approach in the Streamlit page.
-- An "employee" is a cashier observed processing receipts for a business.
--   * active in a fiscal year  -> processed >= 1 receipt for that business that FY
--   * departure in FY N        -> active in FY N but never observed again after it
--   * hire in FY N             -> first observed in FY N
--   * headcount(FY)            -> distinct employees active during that FY
--   * turnover_rate_pct        -> num_left / headcount * 100
--
-- Right-censoring: the most recent fiscal year in the data is flagged
-- (is_censored_period). Every still-employed person's last active year is that
-- final year, so they would all be miscounted as departures. Turnover is left
-- NULL there instead of producing a spurious spike.
with employee_years as (
    select distinct
        business_name,
        cashier_name,
        case when month >= 7 then year else year - 1 end as fiscal_year
    from {{ ref('int_business_employees') }}
),

bounds as (
    select max(fiscal_year) as max_fiscal_year from employee_years
),

headcount as (
    select
        business_name,
        fiscal_year,
        count(distinct cashier_name) as headcount
    from employee_years
    group by business_name, fiscal_year
),

employee_span as (
    select
        business_name,
        cashier_name,
        min(fiscal_year) as first_fiscal_year,
        max(fiscal_year) as last_fiscal_year
    from employee_years
    group by business_name, cashier_name
),

hires as (
    select business_name, first_fiscal_year as fiscal_year, count(*) as num_hired
    from employee_span
    group by business_name, first_fiscal_year
),

departures as (
    select business_name, last_fiscal_year as fiscal_year, count(*) as num_left
    from employee_span
    group by business_name, last_fiscal_year
)

select
    h.business_name,
    h.fiscal_year,
    h.fiscal_year || '-' || (h.fiscal_year + 1)  as fiscal_year_label,
    h.headcount,
    coalesce(hi.num_hired, 0)                    as num_hired,
    coalesce(dp.num_left, 0)                     as num_left,
    (h.fiscal_year = b.max_fiscal_year)          as is_censored_period,
    case
        when h.fiscal_year = b.max_fiscal_year then null
        else round(coalesce(dp.num_left, 0) * 100.0 / nullif(h.headcount, 0), 2)
    end                                          as turnover_rate_pct
from headcount h
cross join bounds b
left join hires      hi on h.business_name = hi.business_name and h.fiscal_year = hi.fiscal_year
left join departures dp on h.business_name = dp.business_name and h.fiscal_year = dp.fiscal_year
order by h.business_name, h.fiscal_year
