---
name: sql-conventions
description: "Convenções de SQL do time: estilo, CTEs, nomes, corretude (grain, fan-out em joins, nulos) e checklist de performance. Use ao escrever ou revisar qualquer SQL."
---

# Convenções de SQL

## Estilo
- Palavras-chave, funções e identificadores em minúsculas. Indentação de 4 espaços. Linhas até 120 caracteres.
- Uma CTE por etapa lógica, nomeada pelo que contém (`orders`, `line_item_agg`), não pelo que faz (`step1`, `tmp`).
- Importe sources e refs em CTEs no topo (`with orders as (select * from {{ ref('stg_tpch__orders') }})`) e transforme depois.
- Uma coluna por linha, vírgula no final da linha, `as` explícito em todo alias.
- Em joins, prefixe colunas com o nome da CTE (`orders.order_key`). Nunca aliases de uma letra.
- `select *` só dentro das CTEs de importação. Nunca no select final de um modelo.

## Nomes
- snake_case em tudo. Chaves terminam em `_key`, datas em `_date`, timestamps em `_at`, booleanos começam com `is_` ou `has_`.
- Valores monetários dizem o que são: `net_amount`, `gross_amount`, `total_price`.
- Agregações nomeadas pelo que medem: `line_count`, `net_revenue`, `late_line_count`.

## Corretude
- Declare o grain de toda query ou modelo (comentário ou description) e garanta que nenhum join o multiplica. Se o lado direito tem várias linhas por chave, agregue antes de juntar.
- `left join` por padrão quando o lado direito pode não ter correspondência. `inner join` só quando a ausência deve excluir a linha, e documente.
- Trate nulos de forma explícita (`coalesce`) nas métricas que vão para marts.
- Compare `date` com `date`. Evite `cast` ou função em cima da coluna no lado esquerdo de um filtro.
- Proteja denominadores: `x / nullif(y, 0)`.
- `distinct` não corrige fan-out, só esconde. Corrija o join.
- Valide o grain com `select chave, count(*) from t group by 1 having count(*) > 1 limit 5`.

## Performance
- Filtre o mais cedo possível, na CTE de importação quando o filtro é fixo.
- Evite funções sobre colunas em `where` e `join`.
- Agregue antes de juntar tabelas grandes.
- Em warehouses com partição ou clustering (BigQuery, Snowflake), filtre pela coluna de partição. No DuckDB local isso não existe, mas escreva como se existisse.
- Em análises ad hoc, use `limit` e veja contagens antes de extrair detalhes.

## Dialeto
Consulte `stack.toml` (skill `stack-profile`). No DuckDB: `date_trunc('month', d)`, `strftime(d, '%Y-%m')`, `quantile_cont`, `list_*`, `year(d)`. Não use funções específicas de outro warehouse sem checar o dialeto.
