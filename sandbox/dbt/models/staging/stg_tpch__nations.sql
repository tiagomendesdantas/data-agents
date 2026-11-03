with source as (
    select * from {{ source('raw', 'nation') }}
)

select
    n_nationkey as nation_key,
    n_name as nation_name,
    n_regionkey as region_key
from source
