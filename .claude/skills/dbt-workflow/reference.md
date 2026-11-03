# Referência dbt

## Materializações
- `view` (padrão em staging): barata, sempre atual, recalcula a cada leitura.
- `table` (padrão em marts): materializa; use quando a query é cara ou consumida por BI/ML.
- `ephemeral`: CTE inline; use em intermediate pequenos que só um modelo consome.
- `incremental`: só quando a tabela é grande e tem uma coluna de evento ou atualização confiável. Padrão:
  ```sql
  {{ config(materialized='incremental', unique_key='order_key') }}
  select ... from {{ ref('stg_tpch__orders') }}
  {% if is_incremental() %}
  where order_date > (select max(order_date) from {{ this }})
  {% endif %}
  ```
  `--full-refresh` reconstrói do zero e é bloqueado fora do sandbox pelo hook.

## Comandos úteis
Todos a partir de `sandbox/dbt`, com `uv run --project .. dbt ... --profiles-dir .`:
- `build --select +modelo`: modelo + upstream, com testes.
- `build --select modelo+`: modelo + downstream.
- `test --select modelo`: só os testes do modelo.
- `run --select tag:x`, `ls --select marts`: seleção por tag ou pasta.
- `docs generate`: gera `target/catalog.json` e `manifest.json` (linhagem em `target/`).
- `parse`: valida o projeto sem tocar no warehouse (útil para revisão).

## Testes singulares
Arquivo `.sql` em `tests/` que retorna as linhas ruins. Vazio = passa. Nomeie `assert_<modelo>_<regra>.sql` e comente a regra na primeira linha.

## Contratos
Para marts consumidos por BI ou ML:
```yaml
- name: fct_orders
  config:
    contract:
      enforced: true
  columns:
    - name: order_key
      data_type: bigint
```
O build falha se o tipo divergir. Use só quando há consumidor que depende do schema.

## Freshness de source
```yaml
sources:
  - name: raw
    freshness:
      warn_after: {count: 24, period: hour}
    loaded_at_field: loaded_at
```
No sandbox os dados são estáticos (1992 a 1998). Não configure freshness contra `now()`; valide contra `max(order_date)` com um teste singular se precisar.

## Erros comuns
- `Could not set lock on file`: outro processo está escrevendo no DuckDB. Espere ele terminar. Nunca apague o `.wal`.
- `Profile sandbox not found`: você não está em `sandbox/dbt` ou esqueceu `--profiles-dir .`.
- `Compilation Error ... depends on a source named 'x'`: fonte não declarada em `models/sources.yml`.
- Schema `main_staging` em vez de `staging`: a macro `generate_schema_name` em `macros/` não foi carregada; confira `macro-paths`.
