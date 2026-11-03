with source as (
    select * from {{ source('raw', 'orders') }}
)

select
    o_orderkey as order_key,
    o_custkey as customer_key,
    o_orderstatus as order_status,
    cast(o_totalprice as decimal(15, 2)) as total_price,
    cast(o_orderdate as date) as order_date,
    o_orderpriority as order_priority,
    o_clerk as clerk,
    o_shippriority as ship_priority
from source
