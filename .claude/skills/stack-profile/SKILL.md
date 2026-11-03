---
name: stack-profile
description: "Fonte da verdade sobre o stack de dados deste repositório (warehouse, dialeto SQL, projeto dbt, ambiente). Leia antes de executar qualquer SQL ou comando dbt."
---

# Stack profile

O arquivo `.claude/skills/stack-profile/stack.toml` (caminho relativo à raiz do repositório) descreve o stack em uso. Leia-o antes de executar SQL ou dbt. Nunca presuma warehouse, dialeto ou caminhos.

## Como usar

1. Leia `stack.toml`. Campos que importam:
   - `env.name`: `sandbox` é local e pode ser destruído e recriado. Qualquer outro nome é ambiente real: nada destrutivo sem confirmação do usuário.
   - `warehouse.type` e `warehouse.dialect`: adapte sintaxe e funções ao dialeto.
   - `warehouse.path`: caminho do arquivo DuckDB (quando `type = "duckdb"`), relativo à raiz.
   - `dbt.project_dir`, `dbt.profiles_dir`, `dbt.target`.
   - `schemas.*`: nomes dos schemas `raw`, `staging` e `marts`.
2. Para SQL ad hoc use o script, nunca `python -c` com SQL embutido:
   ```
   make query q="select count(*) from raw.orders"
   uv run --project sandbox python .claude/skills/stack-profile/scripts/run_sql.py "select 1" [--limit N] [--csv] [--file q.sql] [--write]
   ```
   O script lê `stack.toml`, abre o warehouse somente leitura por padrão (`--write` para gravar) e tenta de novo se o DuckDB estiver travado por outro processo.
3. Para dbt, prefira `make dbt-build` e `make dbt-test`. Para iterar em um modelo:
   ```
   cd sandbox/dbt && uv run --project .. dbt build --profiles-dir . --select +<modelo>
   ```

## Regras

- `env.name != "sandbox"` significa ambiente real: `DROP`, `TRUNCATE`, `DELETE` sem `WHERE`, `UPDATE` sem `WHERE` e `--full-refresh` exigem confirmação explícita do usuário. Um hook também bloqueia.
- O DuckDB aceita um único processo escritor por vez. Não rode `dbt build` em paralelo com outra escrita. Leituras concorrentes funcionam em modo somente leitura.
- Ao trocar de stack, edite apenas `stack.toml` e o `profiles.yml` do dbt. Não espalhe caminhos ou nomes de warehouse pelos agentes.
