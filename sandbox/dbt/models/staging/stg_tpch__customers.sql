with source as (
    select * from {{ source('raw', 'customer') }}
)

select
    c_custkey as customer_key,
    c_name as customer_name,
    c_address as address,
    c_nationkey as nation_key,
    c_phone as phone,
    cast(c_acctbal as decimal(15, 2)) as account_balance,
    c_mktsegment as market_segment,
    c_comment as customer_comment
from source
