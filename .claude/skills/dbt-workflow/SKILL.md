---
name: dbt-workflow
description: "Como criar e alterar modelos dbt neste repositório: camadas (staging, intermediate, marts), nomes, yml com testes e descriptions, comandos de build e definição de pronto. Use em qualquer tarefa que toque o projeto dbt."
---

# Fluxo dbt

Projeto em `sandbox/dbt` (confirme em `stack.toml`). Rode sempre via Makefile ou a partir de `sandbox/dbt` com `--profiles-dir .`.

## Camadas e nomes
| Camada | Pasta | Nome | Materialização | Pode fazer |
|---|---|---|---|---|
| staging | `models/staging/` | `stg_<source>__<entidade>` (plural) | view | renomear, converter tipos, cálculos triviais de uma linha |
| intermediate | `models/intermediate/` | `int_<entidade>_<verbo>` | view ou ephemeral | joins e agregações reutilizáveis, sem semântica final de negócio |
| marts | `models/marts/` | `fct_<evento>`, `dim_<entidade>`, `mart_<assunto>` | table | lógica de negócio, métricas, tabelas largas para BI |

Regras:
- Staging não faz join nem agregação. Um staging por tabela de source.
- Só staging usa `source()`. Todo o resto usa `ref()`.
- Todo modelo tem entrada no yml da pasta (`_staging.yml`, `_marts.yml`) com description que declara o grain ("Grain: 1 linha por order_key") e define as métricas.
- Chave primária: `unique` + `not_null`. Chaves estrangeiras: `relationships`. Enumerações: `accepted_values`.
- Use `data_tests:`, não `tests:`. Testes com parâmetros (`relationships`, `accepted_values`) recebem os parâmetros sob `arguments:`.
- Nunca remova um teste para o build passar. Corrija o modelo ou explique no Relatório.

## Fluxo de trabalho
1. Leia o yml e o SQL dos modelos upstream que vai usar e descubra o grain deles.
2. Escreva o SQL a partir de `templates/model.sql`. Declare o grain em comentário no topo.
3. Escreva ou atualize o yml a partir de `templates/schema.yml`.
4. Rode o build do modelo e dos upstream:
   ```
   cd sandbox/dbt && uv run --project .. dbt build --profiles-dir . --select +<modelo>
   ```
5. Valide o grain com uma query (`group by chave having count(*) > 1` deve retornar 0 linhas).
6. Confira contagens contra o upstream. Um `fct_orders` deve ter o mesmo número de linhas que `stg_tpch__orders`.
7. Relatório com a saída do build e as queries de validação.

## Definição de pronto (dbt)
- `dbt build --select +<modelo>` passa, modelos e testes.
- yml atualizado com description e testes de chave.
- Grain validado por query.
- Nenhum `select *` no select final. Nenhum `source()` fora de staging.

Materializações, incremental, docs e erros comuns: `reference.md` nesta pasta.
