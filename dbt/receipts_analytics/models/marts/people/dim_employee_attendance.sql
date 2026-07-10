-- Q3 support: the roster of distinct employees active per business per month.
-- (Formerly q3/employee_attendences.sql.)
with employees as (
    select distinct
        business_name,
        year,
        month,
        month_name,
        cashier_name
    from {{ ref('int_business_employees') }}
)

select
    business_name,
    year,
    month,
    month_name,
    string_agg(cashier_name, ', ' order by cashier_name) as employees,
    count(*)                                             as num_employees
from employees
group by business_name, year, month, month_name
order by business_name, year, month
