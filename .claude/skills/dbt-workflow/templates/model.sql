-- Grain: 1 linha por <chave>.
-- Descrição curta do que o modelo representa e das métricas principais.

with upstream_a as (
    select * from {{ ref('stg_source__entity') }}
),

upstream_b as (
    select * from {{ ref('stg_source__other') }}
),

aggregated as (
    select
        key_column,
        count(*) as row_count,
        sum(amount) as total_amount
    from upstream_b
    group by key_column
)

select
    upstream_a.key_column,
    upstream_a.some_date,
    coalesce(aggregated.row_count, 0) as row_count,
    coalesce(aggregated.total_amount, 0) as total_amount
from upstream_a
left join aggregated on upstream_a.key_column = aggregated.key_column
