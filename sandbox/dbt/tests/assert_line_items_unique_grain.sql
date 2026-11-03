-- Falha se o grain (order_key, line_number) de stg_tpch__line_items tiver duplicatas.
select
    order_key,
    line_number,
    count(*) as n
from {{ ref('stg_tpch__line_items') }}
group by order_key, line_number
having count(*) > 1
