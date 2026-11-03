# Referência de testes de dados

## Testes genéricos no yml
```yaml
columns:
  - name: order_key
    data_tests: [unique, not_null]
  - name: customer_key
    data_tests:
      - not_null
      - relationships:
          arguments:
            to: ref('dim_customers')
            field: customer_key
  - name: order_status
    data_tests:
      - accepted_values:
          arguments:
            values: ['O', 'F', 'P']
            config:
              severity: warn   # use warn só quando a violação é aceitável e documentada
```

## Teste singular de volume contra o upstream
```sql
-- fct_orders deve ter exatamente uma linha por pedido de stg_tpch__orders.
with expected as (select count(*) as n from {{ ref('stg_tpch__orders') }}),
actual as (select count(*) as n from {{ ref('fct_orders') }})
select expected.n as expected_rows, actual.n as actual_rows
from expected, actual
where expected.n != actual.n
```

## Teste singular de faixa com justificativa
```sql
-- Profile em 2026-11-03: net_revenue entre 0 e 600k; valores acima de 1M indicam erro de join.
select order_key, net_revenue
from {{ ref('fct_orders') }}
where net_revenue > 1000000
```

## Provar que um teste falha quando deve
No sandbox, crie uma tabela temporária ruim e rode a query do teste contra ela:
```
uv run --project sandbox python .claude/skills/stack-profile/scripts/run_sql.py \
  "select order_key, net_revenue from (select 1 as order_key, -5 as net_revenue) where net_revenue < 0"
```
Resultado com 1 linha = o teste pegaria o caso. Registre isso no Relatório.

## Contrato de schema
```yaml
- name: fct_orders
  config:
    contract:
      enforced: true
  columns:
    - name: order_key
      data_type: bigint
    - name: net_revenue
      data_type: decimal(38, 2)
```
Use só quando há consumidor dependente. Tipos devem bater com o que o warehouse cria (confira com `describe`).

## Documentação de colunas
Toda coluna de mart tem `description`. Para PII, adicione `meta`:
```yaml
- name: customer_name
  description: Nome do cliente.
  meta:
    pii: true
    pii_class: direct
    owner: data-team
```

## Anomalias
Sem ferramenta dedicada no sandbox. Abordagem leve: teste singular que compara a métrica do período mais recente com a mediana dos períodos anteriores e falha se desviar mais de X%, com X justificado pelo profile histórico.
