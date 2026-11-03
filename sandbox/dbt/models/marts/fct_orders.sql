with orders as (
    select * from {{ ref('stg_tpch__orders') }}
),

line_items as (
    select * from {{ ref('stg_tpch__line_items') }}
),

line_item_agg as (
    select
        order_key,
        count(*) as line_count,
        sum(quantity) as total_quantity,
        sum(net_amount) as net_revenue,
        sum(case when is_late then 1 else 0 end) as late_line_count
    from line_items
    group by order_key
)

select
    orders.order_key,
    orders.customer_key,
    orders.order_date,
    orders.order_status,
    orders.order_priority,
    orders.total_price,
    coalesce(line_item_agg.line_count, 0) as line_count,
    coalesce(line_item_agg.total_quantity, 0) as total_quantity,
    coalesce(line_item_agg.net_revenue, 0) as net_revenue,
    coalesce(line_item_agg.late_line_count, 0) as late_line_count
from orders
left join line_item_agg on orders.order_key = line_item_agg.order_key
