# DATA_AGENTS

Um time de agentes para tarefas de times de dados, construído com os recursos nativos do Claude Code: subagents, skills e hooks. Vem com um sandbox local (DuckDB + dbt + dados TPC-H sintéticos) para que os agentes possam ser exercitados de ponta a ponta sem credenciais nem infraestrutura.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/): instala o Python 3.12 e as dependências sozinho.
- `make`.
- Claude Code (CLI, app desktop ou extensão do VS Code).

## Setup

```bash
cd DATA_AGENTS
make sandbox        # uv sync + seed TPC-H (sf=0.1) + dbt build
make query q="select count(*) from marts.fct_orders"
```

Abra o Claude Code na raiz do repositório. Tudo que está em `.claude/` é carregado automaticamente: `/agents` lista os seis agentes, `/hooks` mostra os guardrails. Ao iniciar a sessão, um hook avisa se o warehouse ainda não foi semeado.

## Como usar

### Pelo roteador

```
/data crie um mart de receita por cliente com testes
/data ingira sandbox/data/fx_rates.csv em raw.fx_rates e crie o staging
/data treine um baseline para prever se uma linha de pedido vai atrasar
/data classifique PII nos modelos e documente as colunas
```

O `/data` roda na sessão principal. Ele faz a triagem da tarefa, delega aos agentes certos (em sequência quando há dependência ou escrita no warehouse, em paralelo quando é só leitura), chama o `data-reviewer` para tudo que alterou código e devolve um relatório consolidado.

### Diretamente

```
@agent-data-analyst quanto faturamos por região em 1995?
/data-review                 # revisa tudo que está modificado ou não rastreado no git
/data-review --staged        # só o que está no stage
/data-review sandbox/dbt     # só um caminho
```

Perguntas de negócio costumam ser delegadas automaticamente ao `data-analyst`, sem precisar do `/data`.

## O time

| Agente | Papel | Escreve em | Modelo |
|---|---|---|---|
| `data-engineer` | ingestão, pipelines, scripts de carga, performance | `sandbox/pipelines/`, `sandbox/tests/` | herda da sessão |
| `analytics-engineer` | modelos dbt, yml, métricas | `sandbox/dbt/models/` | herda da sessão, memória de projeto |
| `data-analyst` | perguntas de negócio, EDA, gráficos | `sandbox/analyses/`, `sandbox/notebooks/` (hook bloqueia o resto) | sonnet |
| `data-scientist` | experimentos, features, treino e avaliação | `sandbox/ml/`, `sandbox/experiments/`, `sandbox/notebooks/` | herda da sessão, effort alto |
| `data-quality-engineer` | testes de dados, contratos, PII, documentação | yml dos modelos, `sandbox/dbt/tests/` | sonnet |
| `data-reviewer` | revisão somente leitura, veredito APROVADO / COM RESSALVAS / BLOQUEADO | nada | herda da sessão, effort alto, memória de projeto |

Os subagents não delegam entre si. Quando uma tarefa foge do papel, o agente encerra com "Próximo agente sugerido" no Relatório e a sessão principal decide.

Para ajustar modelo, limite de turnos ou ferramentas de um agente, edite o frontmatter do arquivo correspondente em `.claude/agents/`.

## Skills

| Skill | Conteúdo | Quem carrega |
|---|---|---|
| `stack-profile` | `stack.toml` (fonte da verdade do stack) e `scripts/run_sql.py` | todos |
| `team-conventions` | bloco Relatório, definição de pronto, hand-offs, limites | todos |
| `sql-conventions` | estilo, nomes, grain, fan-out, performance | engenheiros, analista, revisor |
| `dbt-workflow` | camadas, nomes, yml, comandos, templates | analytics, qualidade, revisor |
| `data-quality-checks` | catálogo de testes, PII, `scripts/profile_table.py` | analytics, qualidade, revisor |
| `eda-protocol` | pergunta, fonte, validação, template de análise | analista, cientista |
| `ml-experiment` | baseline, split temporal, leakage, template de experimento | cientista |
| `data` | comando `/data` (roteador) | sessão principal |
| `data-review` | comando `/data-review` (fork no revisor) | sessão principal |

## Guardrails

- **`sql_guard.py`** (hook `PreToolUse` em Bash): só age quando o comando invoca um cliente SQL (duckdb, psql, bq, snowsql, dbt run-operation, `run_sql.py`) ou `dbt run/build --full-refresh`. Com `env.name = "sandbox"` em `stack.toml`, libera duckdb, dbt e `run_sql.py`. Fora do sandbox: `DROP SCHEMA/DATABASE` e `TRUNCATE` são negados; `DROP TABLE`, `DELETE`/`UPDATE` sem `WHERE`, `ALTER ... DROP` e `--full-refresh` pedem confirmação. Clientes de warehouse externo (psql, bq, snowsql) nunca são tratados como sandbox.
- **`guard_paths.sh`** (hook no frontmatter do `data-analyst`): bloqueia Write/Edit fora de `sandbox/analyses` e `sandbox/notebooks`.
- **`permissions.deny`** em `.claude/settings.json`: `.env*`, `~/.dbt/`, `*.pem`, `secrets/`, credenciais de gcloud e snowflake.
- **`session_start.sh`**: mostra o `env.name` ativo e avisa se o warehouse não existe.

Para aprovar uma exceção, responda ao prompt de confirmação. Para testar o comportamento sem sandbox, mude `env.name` para outro valor e tente um `make query q="drop table raw.region" --write`.

Limites conhecidos do guard: não vê SQL montado dinamicamente em `python -c`, não distingue palavra-chave dentro de string literal, e um comando que apenas cita um cliente e uma palavra destrutiva (por exemplo `git commit -m "fix psql truncate"`) também dispara. É cinto de segurança, não cerca.

## Sandbox

- `sandbox/seed.py` gera TPC-H com `sf=0.1` pela extensão `tpch` do DuckDB: 150.000 pedidos, 600.572 itens, 15.000 clientes, 25 países, 5 regiões. Idempotente; `--force` regenera.
- Projeto dbt em `sandbox/dbt`: 5 staging (`stg_tpch__*`), 2 marts (`dim_customers`, `fct_orders`), 40 testes genéricos e 2 singulares. `profiles.yml` é commitado porque não tem segredos.
- Os dados são de 1992 a 1998 e estáticos. Checks de freshness não devem usar `now()`.

## Trocar de stack

1. Edite `.claude/skills/stack-profile/stack.toml`: `env.name` (qualquer valor diferente de `sandbox` ativa o modo cauteloso), `warehouse.*`, `dbt.*`, `schemas.*`.
2. Troque o adapter do dbt (`dbt-bigquery`, `dbt-snowflake`, `dbt-postgres`) em `sandbox/pyproject.toml` ou num projeto dbt próprio, e crie o `profiles.yml` com credenciais fora do repositório (`~/.dbt/`), que já está no `permissions.deny`.
3. `run_sql.py` e `profile_table.py` suportam DuckDB. Para outro warehouse, adicione um conector nesses dois scripts; eles são o único ponto de acesso ad hoc.
4. Os agentes e skills não precisam mudar: todos leem o `stack.toml`.

## Roadmap: empacotar como plugin

Quando for compartilhar com o time:

```
git mv .claude/agents agents
git mv .claude/skills skills
git mv .claude/hooks hooks
```

Depois crie `.claude-plugin/plugin.json`, gere `hooks/hooks.json` a partir do bloco `hooks` de `settings.json` trocando `$CLAUDE_PROJECT_DIR` por `${CLAUDE_PLUGIN_ROOT}`, mova o conteúdo do `CLAUDE.md` para a skill `team-conventions` (CLAUDE.md na raiz de um plugin não é carregado), recrie o guard de caminho do analista em `hooks/hooks.json` (agentes de plugin ignoram `hooks` no frontmatter), e documente o `permissions.deny` para cada projeto consumidor (plugins não distribuem permissões). O sandbox vira `examples/sandbox/`. Valide com `claude plugin validate .` e teste com `claude --plugin-dir .`.

## Cenários de aceitação

Use para validar o time depois de qualquer mudança nos agentes ou skills.

| # | O que digitar | Esperado |
|---|---|---|
| 1 | `Quanto faturamos por região em 1995?` | delegação automática ao `data-analyst`; arquivo em `sandbox/analyses/` com SQL, tabela e validação; sem revisor |
| 2 | `/data crie um mart de receita por cliente com testes` | analytics-engineer, depois quality, depois reviewer; `mart_customer_revenue.sql` e yml; saída do `dbt build` no relatório |
| 3 | `/data ingira sandbox/data/fx_rates.csv em raw.fx_rates e crie o staging` | data-engineer, depois analytics-engineer, depois reviewer; script em `pipelines/`, teste em `tests/`, `stg_fx_rates.sql` |
| 4 | `/data treine um baseline para prever se uma linha de pedido vai atrasar` | data-scientist, depois reviewer; registro em `experiments/`, script em `ml/` |
| 5 | editar `fct_orders.sql` à mão com um join que duplica linhas, depois `/data-review` | veredito `BLOQUEADO` citando o join |
| 6 | `/data classifique PII nos modelos e documente colunas` | quality, depois reviewer; `meta: {pii: true}` em `customer_name`, `address`, `phone` |
| 7 | com `env.name = "prod"` em `stack.toml`, pedir para apagar `raw.orders` | o hook pede confirmação ou nega |

## Troubleshooting

- `Could not set lock on file`: outro processo está escrevendo no DuckDB (um `dbt build` em andamento, por exemplo). Espere terminar. Nunca apague o arquivo `.wal`.
- `warehouse não encontrado`: rode `make seed`.
- `warning: VIRTUAL_ENV=... does not match the project environment path`: você tem um ambiente conda ou venv ativo no shell. É só um aviso do `uv`; os alvos do Makefile já o silenciam.
- O hook bloqueou um comando legítimo: confira se o comando cita um cliente SQL e uma palavra destrutiva ao mesmo tempo. Reescreva o comando ou confirme no prompt.
- Um agente não aparece em `/agents`: valide o frontmatter YAML do arquivo em `.claude/agents/` (nome deve ser igual ao nome do arquivo).
