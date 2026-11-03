-- Falha se algum pedido tiver receita líquida negativa.
select
    order_key,
    net_revenue
from {{ ref('fct_orders') }}
where net_revenue < 0
