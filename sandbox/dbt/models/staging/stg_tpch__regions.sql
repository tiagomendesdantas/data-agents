with source as (
    select * from {{ source('raw', 'region') }}
)

select
    r_regionkey as region_key,
    r_name as region_name
from source
