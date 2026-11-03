with source as (
    select * from {{ source('raw', 'lineitem') }}
)

select
    l_orderkey as order_key,
    l_linenumber as line_number,
    l_partkey as part_key,
    l_suppkey as supplier_key,
    l_quantity as quantity,
    cast(l_extendedprice as decimal(15, 2)) as extended_price,
    l_discount as discount,
    l_tax as tax,
    cast(l_extendedprice * (1 - l_discount) as decimal(15, 2)) as net_amount,
    l_returnflag as return_flag,
    l_linestatus as line_status,
    cast(l_shipdate as date) as ship_date,
    cast(l_commitdate as date) as commit_date,
    cast(l_receiptdate as date) as receipt_date,
    l_receiptdate > l_commitdate as is_late,
    l_shipinstruct as ship_instructions,
    l_shipmode as ship_mode
from source
