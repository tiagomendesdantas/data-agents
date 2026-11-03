# DATA_AGENTS

Um time de agentes para tarefas de times de dados, rodando dentro do Claude Code. Você descreve a tarefa em português, um roteador decide quem faz o quê, os agentes executam no seu repositório e um revisor somente leitura dá o veredito antes de qualquer coisa ser considerada pronta.

Vem com um sandbox local (DuckDB + dbt + dados sintéticos TPC-H) para você testar tudo sem credenciais nem infraestrutura. Quando tiver um warehouse real, a troca é um arquivo de configuração.

## O que vem na caixa

| Agente | Chame quando quiser | O que ele entrega |
|---|---|---|
| `data-analyst` | responder uma pergunta de negócio, explorar dados, comparar períodos, um gráfico | um arquivo em `sandbox/analyses/` com a pergunta, o SQL, o resultado, as validações e os caveats |
| `analytics-engineer` | criar ou mudar um modelo dbt, definir uma métrica, documentar um mart | SQL + yml com grain, descriptions e testes, e a saída do `dbt build` |
| `data-engineer` | ingerir um arquivo ou fonte nova, escrever um pipeline, melhorar performance | script em `sandbox/pipelines/`, teste em `sandbox/tests/`, tabela em `raw` |
| `data-quality-engineer` | adicionar testes de dados, contratos, classificar PII, completar documentação | testes no yml e em `sandbox/dbt/tests/`, tags `meta.pii`, saída do `dbt test` |
| `data-scientist` | um experimento de ML, features, baseline, avaliação | script em `sandbox/ml/`, registro em `sandbox/experiments/`, notebook opcional |
| `data-reviewer` | revisar o que foi alterado antes de aceitar | veredito `APROVADO`, `APROVADO COM RESSALVAS` ou `BLOQUEADO`, com achados por arquivo e linha |

Dois comandos: `/data <tarefa>` orquestra o time inteiro; `/data-review` chama só o revisor.

## Instalação

Pré-requisitos: [uv](https://docs.astral.sh/uv/), `make` e o Claude Code (CLI, app ou extensão do VS Code).

```bash
git clone https://github.com/tiagomendesdantas/data-agents.git
cd data-agents
make sandbox
```

O `make sandbox` instala o Python 3.12 e as dependências, gera o warehouse local com dados TPC-H (150 mil pedidos, 600 mil itens) e roda o `dbt build`. Ao final você deve ver `PASS=47`.

Confira que o sandbox responde:

```bash
make query q="select region_name, count(*) as customers from marts.dim_customers group by 1"
```

Agora abra o Claude Code na raiz do repositório. Tudo em `.claude/` é carregado sozinho. Para confirmar:

- `/agents` lista os seis agentes.
- `/hooks` mostra os guardrails ativos.
- Na abertura da sessão aparece uma linha `[data-agents] stack.toml env.name=sandbox`.

## Primeiro uso

Há três jeitos de pedir trabalho. Comece pelo primeiro.

### 1. Pergunte, como perguntaria a uma pessoa

```
Quanto faturamos por região em 1995?
```

O Claude Code reconhece uma pergunta de negócio e delega ao `data-analyst` sem você precisar nomeá-lo. O analista lê o yml dos modelos, consulta os marts, valida o número e grava um arquivo em `sandbox/analyses/2026-11-03_receita_por_regiao.md` com a query e os caveats. A resposta no chat sempre vem com o SQL que gerou o número.

### 2. Use `/data` para tarefas com mais de um passo

```
/data crie um mart de receita por cliente com testes
```

O `/data` roda na sessão principal e segue sempre o mesmo roteiro:

1. **Triagem:** quebra a tarefa em itens e decide o agente de cada um. Se faltar algo essencial (período, métrica, tabela), pergunta uma vez, tudo junto.
2. **Plano:** mostra em poucas linhas o que vai fazer e em que ordem.
3. **Delegação:** chama os agentes. Em sequência quando um depende do outro ou quando os dois escrevem no warehouse; em paralelo quando é só leitura.
4. **Revisão:** se algum arquivo foi alterado, o `data-reviewer` revisa. Se bloquear, o agente dono corrige e a revisão roda de novo (até duas vezes; depois o problema volta para você).
5. **Relatório final:** arquivos alterados, comandos executados com resultado, veredito, caveats e próximos passos.

Mais exemplos que funcionam no sandbox:

```
/data ingira sandbox/data/fx_rates.csv em raw.fx_rates e crie o staging
/data classifique PII nos modelos e documente as colunas que faltam
/data treine um baseline para prever se uma linha de pedido vai atrasar
/data adicione um teste de volume no fct_orders comparando com o staging
```

### 3. Fale com um agente específico

```
@agent-analytics-engineer refatore o fct_orders para incluir o total de impostos
@agent-data-quality-engineer perfile marts.dim_customers e proponha testes
```

Útil quando você já sabe quem deve fazer. Não passa pelo revisor automaticamente; chame `/data-review` depois.

### Revisar antes de aceitar

```
/data-review                 # tudo que está modificado ou novo no git
/data-review --staged        # só o que está no stage
/data-review sandbox/dbt     # só um caminho
```

## Exemplo do início ao fim

Um fluxo completo num sandbox recém-instalado. A redação dos agentes varia a cada execução; os números são os reais do sandbox e devem bater quando você reproduzir.

**Objetivo:** um mart com a receita líquida por cliente, com testes, e saber quem são os três maiores clientes.

**1. Você digita**

```
/data crie um mart de receita por cliente com testes e me diga os 3 maiores clientes
```

**2. A sessão principal faz a triagem e mostra o plano**

```
Plano
1. analytics-engineer: criar marts/mart_customer_revenue (1 linha por cliente), yml e testes de chave
2. data-quality-engineer: perfilar o mart e adicionar testes de reconciliação      [depois do 1]
3. data-analyst: top 3 clientes lendo o mart                                        [em paralelo com o 2, só leitura]
4. data-reviewer: revisar os itens 1 e 2
Suposição: receita líquida = soma de net_revenue de fct_orders (após desconto, antes de impostos).
```

**3. O `analytics-engineer` cria o modelo** e termina com o Relatório:

```
## Relatório
**Objetivo:** mart_customer_revenue, 1 linha por customer_key
**Arquivos:** sandbox/dbt/models/marts/mart_customer_revenue.sql, sandbox/dbt/models/marts/_marts.yml
**Comandos executados:** dbt build --select +mart_customer_revenue -> 8 models, 43 tests, PASS
**Evidências:** 10.000 linhas; 0 chaves duplicadas; soma de net_revenue = 20.535.072.329,05, igual à soma em fct_orders
**Pendências / riscos:** nenhuma
**Próximo agente sugerido:** data-quality-engineer
```

**4. Qualidade e análise rodam em paralelo.** O primeiro só escreve yml e testes; o segundo só lê o warehouse.

```
## Relatório (data-quality-engineer)
**Arquivos:** sandbox/dbt/tests/assert_mart_customer_revenue_matches_fct_orders.sql; _marts.yml (not_null em net_revenue e order_count)
**Comandos executados:** profile_table.py marts.mart_customer_revenue -> net_revenue 0% nulos, max 5.570.474,03; dbt test --select mart_customer_revenue -> 5 tests PASS
**Evidências:** o teste de reconciliação retorna 1 linha quando invertido e 0 linhas nos dados atuais
```

```
## Relatório (data-analyst)
**Arquivos:** sandbox/analyses/2026-11-03_top3_clientes.md
**Evidências:**
customer_key | customer_name      | region_name | order_count | net_revenue
8362         | Customer#000008362 | EUROPE      | 35          | 5.570.474,03
9454         | Customer#000009454 | AFRICA      | 35          | 5.161.888,62
6958         | Customer#000006958 | AFRICA      | 30          | 5.149.570,48
Validação: a soma dos 10.000 clientes do mart é 20.535.072.329,05, igual ao total de fct_orders.
```

**5. O `data-reviewer` bloqueia**

```
Veredito: BLOQUEADO

Achados:
[alta] sandbox/dbt/models/marts/mart_customer_revenue.sql:4 - o mart parte de fct_orders, então os 5.000 clientes sem pedido ficam de fora (10.000 linhas contra 15.000 em dim_customers), mas a description promete "1 linha por cliente" - parta de dim_customers com left join e coalesce(net_revenue, 0)
[baixa] sandbox/dbt/models/marts/_marts.yml:92 - coluna order_count sem description

Verificações executadas:
- dbt parse -> ok
- select count(*) from marts.dim_customers -> 15.000; from marts.mart_customer_revenue -> 10.000
```

**6. A sessão principal devolve os achados ao `analytics-engineer`.** Ele reescreve o modelo partindo de `dim_customers`, roda o build de novo (15.000 linhas, 5.000 delas com receita 0) e o revisor aprova na segunda rodada. O teste de reconciliação continua passando porque a soma não mudou.

**7. Relatório final no chat**

```
## Resultado
**Tarefa:** mart de receita por cliente com testes, e os 3 maiores clientes
**Arquivos alterados:**
- sandbox/dbt/models/marts/mart_customer_revenue.sql (novo)
- sandbox/dbt/models/marts/_marts.yml
- sandbox/dbt/tests/assert_mart_customer_revenue_matches_fct_orders.sql (novo)
- sandbox/analyses/2026-11-03_top3_clientes.md (novo)
**Verificações:** dbt build --select +mart_customer_revenue -> PASS; dbt test --select mart_customer_revenue -> 5 tests PASS; soma do mart = soma de fct_orders
**Revisão:** APROVADO na 2ª rodada (a 1ª bloqueou por grain incompleto, corrigido)
**Caveats:** receita líquida é após desconto e antes de impostos; 5.000 clientes aparecem com receita 0 por não terem pedidos
**Próximos passos:** se o BI precisar de receita por ano, criar mart_customer_revenue_yearly com grain cliente-ano

Os 3 maiores clientes: Customer#000008362 (EUROPE, 5.570.474,03), Customer#000009454 (AFRICA, 5.161.888,62) e Customer#000006958 (AFRICA, 5.149.570,48).
```

**8. O que ficou no repositório**

```
$ git status --short
 M sandbox/dbt/models/marts/_marts.yml
?? sandbox/analyses/2026-11-03_top3_clientes.md
?? sandbox/dbt/models/marts/mart_customer_revenue.sql
?? sandbox/dbt/tests/assert_mart_customer_revenue_matches_fct_orders.sql
```

Revise o diff, rode `/data-review --staged` se quiser uma segunda olhada, e faça o commit. Para reproduzir, digite o comando do passo 1 num sandbox recém-instalado.

## Como ler o que os agentes devolvem

**Bloco Relatório.** Todo agente termina com um bloco fixo: objetivo, arquivos, comandos executados com resultado, evidências (contagens, saídas), pendências e "Próximo agente sugerido". Se um agente não executou o que criou, ele diz isso no bloco em vez de declarar pronto.

**Próximo agente sugerido.** Os agentes não delegam entre si. Quando a tarefa sai do papel deles, param e apontam quem deveria continuar. Com `/data`, a sessão principal cuida disso; se você chamou o agente direto, é você quem chama o próximo.

**Veredito do revisor.**

```
Veredito: BLOQUEADO

Achados:
[alta] sandbox/dbt/models/marts/fct_orders.sql:31 - join com line_items multiplica linhas por pedido - agregue line_items por order_key antes do join
[baixa] sandbox/dbt/models/marts/_marts.yml:40 - coluna total_tax sem description - adicione

Verificações executadas:
- dbt parse -> ok
- select order_key, count(*) ... having count(*) > 1 -> 3.412 linhas
```

`BLOQUEADO` só aparece com achado de severidade alta: resultado errado, fan-out, teste removido, PII exposta, segredo em código. `APROVADO COM RESSALVAS` quando só há média e baixa.

## Receitas

**Responder uma pergunta de negócio.** Pergunte direto. Se o analista disser que falta um modelo para responder com segurança, ele indica o `analytics-engineer`; peça `/data crie o modelo X` e repita a pergunta.

**Criar ou mudar um modelo dbt.** `/data crie um mart ...` ou `@agent-analytics-engineer ...`. O agente lê os modelos upstream, declara o grain, escreve SQL e yml, roda `dbt build --select +modelo` e valida o grain por query. Confira a saída do build no Relatório.

**Ingerir um arquivo novo.** Coloque o arquivo em `sandbox/data/` e peça `/data ingira sandbox/data/<arquivo> em raw.<tabela> e crie o staging`. O engenheiro de dados escreve um script idempotente e um teste; o engenheiro de analytics cria o staging; o revisor fecha.

**Adicionar testes ou classificar PII.** `/data classifique PII nos modelos` ou `/data adicione testes em <modelo>`. O engenheiro de qualidade perfila a tabela antes de propor qualquer teste e prova que cada teste novo falha num caso ruim.

**Rodar um experimento.** `/data treine um baseline para prever <alvo>`. O cientista define alvo e unidade de predição, faz split temporal, mede um baseline antes do modelo e registra tudo em `sandbox/experiments/`. O script em `sandbox/ml/` roda com `uv run --project sandbox python sandbox/ml/<slug>.py`.

**Revisar antes de commitar.** `/data-review --staged`. Se vier `BLOQUEADO`, peça ao agente dono para corrigir citando os achados.

## Comandos do sandbox

| Comando | O que faz |
|---|---|
| `make sandbox` | setup completo: dependências, seed, dbt build |
| `make seed` | regenera os dados TPC-H (idempotente; `--force` no script para recriar) |
| `make dbt-build` / `make dbt-test` | modelos e testes |
| `make query q="..."` | SQL ad hoc, somente leitura |
| `make lint` / `make test` | ruff + sqlfluff / pytest |
| `make clean` | apaga `target/` e `logs/` do dbt; não toca no warehouse |

O warehouse fica em `sandbox/warehouse.duckdb` (fora do git). Os dados vão de 1992 a 1998 e são estáticos: não faça checks de freshness contra a data de hoje.

Modelos que já existem: `stg_tpch__customers`, `stg_tpch__nations`, `stg_tpch__regions`, `stg_tpch__orders`, `stg_tpch__line_items`, `dim_customers`, `fct_orders`.

## Guardrails

Quatro proteções rodam sozinhas:

- **SQL destrutivo** (`.claude/hooks/sql_guard.py`): com `env.name = "sandbox"` em `stack.toml`, `DROP`, `DELETE` e afins são liberados no DuckDB local. Com qualquer outro valor, `DROP SCHEMA` e `TRUNCATE` são negados e o resto pede sua confirmação. Clientes de warehouse externo (`psql`, `bq`, `snowsql`) nunca contam como sandbox.
- **Escrita do analista** (`guard_paths.sh`): o `data-analyst` só grava em `sandbox/analyses/` e `sandbox/notebooks/`.
- **Segredos** (`permissions.deny` em `.claude/settings.json`): `.env*`, `~/.dbt/`, `*.pem`, `secrets/`, credenciais de gcloud e snowflake nunca são lidos.
- **Revisão obrigatória**: o `/data` não encerra uma tarefa que alterou código sem veredito do revisor.

Para liberar uma exceção pontual, responda ao prompt de confirmação. O guard tem limites: não vê SQL montado dentro de `python -c` e dispara também quando um comando só cita um cliente SQL e uma palavra destrutiva juntos (um `git commit -m "fix psql truncate"`, por exemplo). Reescreva o comando ou confirme.

## Personalizar

**Modelo, esforço e limite de turnos de um agente.** Edite o frontmatter em `.claude/agents/<nome>.md`: `model` (`inherit`, `sonnet`, `opus`, `haiku`), `effort`, `maxTurns`. Hoje o analista e o engenheiro de qualidade usam `sonnet`; os demais herdam o modelo da sessão.

**Convenções.** As regras que os agentes seguem estão em `.claude/skills/`: SQL em `sql-conventions`, dbt em `dbt-workflow`, testes e PII em `data-quality-checks`, análise em `eda-protocol`, experimentos em `ml-experiment`, formato de relatório em `team-conventions`. Mudou uma convenção, mudou o comportamento de todos que carregam a skill.

**Agente novo.** Crie `.claude/agents/<nome>.md` com `name`, `description` (diga quando usar e quando não usar; é o que dispara a delegação automática), `tools`, `skills` (inclua `stack-profile` e `team-conventions`) e o prompt. Adicione uma linha na triagem de `.claude/skills/data/SKILL.md` para o `/data` saber quando chamá-lo.

**Trocar de stack.** Edite `.claude/skills/stack-profile/stack.toml` (`env.name`, `warehouse.*`, `dbt.*`), troque o adapter do dbt (`dbt-bigquery`, `dbt-snowflake`, `dbt-postgres`) e crie o `profiles.yml` com credenciais fora do repositório, em `~/.dbt/`. Os scripts `run_sql.py` e `profile_table.py` suportam DuckDB; para outro warehouse, adicione um conector neles. Os agentes não precisam mudar. Qualquer `env.name` diferente de `sandbox` liga o modo cauteloso do guard.

## Compartilhar com o time

Hoje o time vive em `.claude/` deste repositório. Para distribuir como plugin do Claude Code:

```
git mv .claude/agents agents
git mv .claude/skills skills
git mv .claude/hooks hooks
```

Depois crie `.claude-plugin/plugin.json`, converta o bloco `hooks` de `settings.json` em `hooks/hooks.json` (trocando `$CLAUDE_PROJECT_DIR` por `${CLAUDE_PLUGIN_ROOT}`), mova o conteúdo do `CLAUDE.md` para a skill `team-conventions`, recrie o guard de caminho do analista em `hooks/hooks.json` e documente o `permissions.deny` para cada projeto que instalar o plugin. Valide com `claude plugin validate .` e teste com `claude --plugin-dir .`.

## Checklist de validação

Rode depois de mudar agentes ou skills:

| # | O que digitar | Esperado |
|---|---|---|
| 1 | `Quanto faturamos por região em 1995?` | delegação automática ao analista; arquivo em `sandbox/analyses/`; sem revisor |
| 2 | `/data crie um mart de receita por cliente com testes` | analytics, qualidade, revisor; `mart_customer_revenue.sql` e yml; build no relatório |
| 3 | `/data ingira sandbox/data/fx_rates.csv em raw.fx_rates e crie o staging` | engenharia, analytics, revisor; script, teste e `stg_fx_rates.sql` |
| 4 | `/data treine um baseline para prever se uma linha de pedido vai atrasar` | cientista, revisor; registro em `experiments/`, script em `ml/` |
| 5 | editar `fct_orders.sql` com um join que duplica linhas e rodar `/data-review` | `BLOQUEADO` citando o join |
| 6 | `/data classifique PII nos modelos` | qualidade, revisor; `meta: {pii: true}` em nome, endereço e telefone |
| 7 | com `env.name = "prod"` em `stack.toml`, pedir para apagar `raw.orders` | o guard pede confirmação ou nega |

## Problemas comuns

- **`Could not set lock on file`**: outro processo está escrevendo no DuckDB (um `dbt build` em andamento). Espere terminar. Nunca apague o arquivo `.wal`.
- **`warehouse não encontrado`**: rode `make seed`.
- **`warning: VIRTUAL_ENV=... does not match`**: há um conda ou venv ativo no seu shell. É só um aviso do `uv`; os alvos do Makefile já o silenciam.
- **Um agente não aparece em `/agents`**: o frontmatter YAML tem erro. Descriptions com dois-pontos precisam de aspas, e o `name` tem que ser igual ao nome do arquivo.
- **Uma skill não carrega**: mesma causa. Teste com `python -c "import yaml; ..."` ou peça ao Claude para validar o frontmatter.
- **O hook bloqueou um comando legítimo**: veja a seção Guardrails.

## Estrutura do repositório

```
.claude/
  agents/        os seis agentes (um arquivo .md cada)
  skills/        convenções compartilhadas, stack.toml, scripts auxiliares, comandos /data e /data-review
  hooks/         sql_guard.py, guard_paths.sh, session_start.sh
  settings.json  permissões e registro dos hooks
sandbox/
  dbt/           projeto dbt: sources, staging, marts, tests, macros
  seed.py        gera os dados TPC-H
  data/          arquivos de entrada de exemplo
  pipelines/ tests/ analyses/ notebooks/ experiments/ ml/   saídas dos agentes
CLAUDE.md        regras que valem para a sessão principal e para todos os agentes
Makefile         entrada canônica para tudo do sandbox
```
