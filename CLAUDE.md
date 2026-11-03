# DATA_AGENTS

Time de agentes do Claude Code para tarefas de dados (engenharia, analytics, qualidade e governança, ciência de dados), com um sandbox local (DuckDB + dbt + dados TPC-H) para validar o trabalho dos agentes. Documentação, relatórios e descriptions em português do Brasil; código, identificadores e nomes de arquivos em inglês.

## Comandos
- `make sandbox`: instala dependências, semeia o warehouse e roda `dbt build`. Rode uma vez.
- `make dbt-build` e `make dbt-test`: modelos e testes do dbt.
- `make query q="select 1"`: SQL ad hoc, somente leitura.
- `make lint` e `make test`: ruff + sqlfluff, e pytest.
- Python sempre via `uv run --project sandbox`. Nunca `pip`, nunca o Python do sistema.

## Agentes (`.claude/agents/`)
| Agente | Faz | Não faz |
|---|---|---|
| `data-engineer` | ingestão, pipelines, performance | modelos dbt |
| `analytics-engineer` | modelos dbt, yml, métricas | ingestão, análises |
| `data-analyst` | perguntas de negócio, EDA, gráficos | alterar modelos; escreve só em `sandbox/analyses` e `sandbox/notebooks` |
| `data-scientist` | experimentos, features, treino e avaliação | modelos dbt |
| `data-quality-engineer` | testes de dados, contratos, PII, documentação | code review, lógica de modelos |
| `data-reviewer` | revisão somente leitura com veredito | editar qualquer arquivo |

Comandos: `/data <tarefa>` (triagem, delegação, revisão, relatório consolidado) e `/data-review [escopo]`.

## Regras invioláveis
- `.claude/skills/stack-profile/stack.toml` é a fonte da verdade sobre o stack. `env.name = "sandbox"` libera operações destrutivas no DuckDB local; qualquer outro valor é tratado como ambiente real.
- Fora do sandbox, SQL destrutivo (DROP, TRUNCATE, DELETE ou UPDATE sem WHERE, `--full-refresh`) pede confirmação ou é negado pelo hook `.claude/hooks/sql_guard.py`. Não contorne o hook.
- Segredos nunca são lidos: `.env*`, `~/.dbt/`, chaves. Está em `permissions.deny` de `.claude/settings.json`.
- Toda alteração de código passa pelo `data-reviewer` antes de ser considerada pronta.
- O DuckDB aceita um escritor por vez: nunca dois agentes gravando no warehouse ao mesmo tempo.
- Nenhum número é reportado sem a query que o gerou.
- Subagents não delegam entre si. Quem orquestra é a sessão principal, via `/data`.

## Estrutura
```
.claude/agents/        6 subagents
.claude/skills/        skills compartilhadas e os comandos /data e /data-review
.claude/hooks/         sql_guard.py, guard_paths.sh, session_start.sh
sandbox/dbt/           projeto dbt (sources, staging, marts, tests)
sandbox/pipelines/     scripts de ingestão          sandbox/tests/        pytest
sandbox/analyses/      análises do analista         sandbox/notebooks/    notebooks
sandbox/experiments/   registros de experimentos    sandbox/ml/           scripts de ML
sandbox/data/          arquivos de entrada de exemplo
```

## Definição de pronto
Artefato no caminho combinado, executado no sandbox com a saída mostrada, testes passando, e o bloco Relatório no final da resposta (skill `team-conventions`).
