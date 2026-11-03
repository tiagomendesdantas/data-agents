---
name: team-conventions
description: "Convenções do time de agentes de dados: formato do bloco Relatório, definição de pronto, hand-offs entre agentes, idioma e limites de segurança. Pré-carregada em todos os agentes do time."
---

# Convenções do time

## Idioma
- Relatórios, descriptions em yml, documentação e comentários: português do Brasil.
- Código, identificadores, nomes de modelos, colunas e arquivos: inglês.

## Definição de pronto
Uma tarefa só está pronta quando:
1. O artefato existe no caminho combinado.
2. Você executou o que criou no sandbox (query, `dbt build --select`, `pytest`) e a saída está no Relatório.
3. Os testes relevantes passam, ou a falha está explicada no Relatório.
4. O bloco Relatório está no final da sua resposta.

Nunca declare pronto com base só em leitura de código. Se não conseguiu executar, diga isso e por quê.

## Bloco Relatório (obrigatório ao final de toda tarefa)
```
## Relatório
**Objetivo:** <1 linha>
**Arquivos:** <criados/alterados, um por linha, caminho relativo à raiz>
**Comandos executados:** <comando -> resultado resumido, ex.: `make dbt-build` -> 7 models, 26 tests PASS>
**Evidências:** <números, contagens e saídas que provam que funcionou>
**Pendências / riscos:** <o que ficou de fora, suposições feitas, o que precisa de decisão humana>
**Próximo agente sugerido:** <nome do agente ou "nenhum">
```

## Hand-offs
Você não delega para outros agentes. Quando algo está fora do seu papel, não faça: pare e registre em "Próximo agente sugerido".
- Ingestão, pipelines, Python de carga, performance de jobs: `data-engineer`
- Modelos dbt, métricas, yml de modelos: `analytics-engineer`
- Perguntas de negócio, EDA, gráficos: `data-analyst`
- Experimentos e ML: `data-scientist`
- Testes de dados, contratos, PII, catálogo: `data-quality-engineer`
- Revisão de diffs: `data-reviewer` (a sessão principal chama; você não chama)

## Segurança e limites
- Nunca leia `.env*`, `profiles.yml` fora do sandbox, chaves, tokens ou credenciais.
- Se `env.name != "sandbox"` em `stack.toml`, nada destrutivo sem confirmação explícita do usuário.
- Um só processo escreve no DuckDB por vez: não rode `dbt build` enquanto outra escrita estiver em curso. Para leitura use `run_sql.py` (somente leitura por padrão).
- Não instale dependências novas sem registrar no Relatório. Prefira o que já está em `sandbox/pyproject.toml`.
- Não invente números: todo valor reportado vem de uma query ou saída de comando mostrada.
- Não altere `stack.toml`, `.claude/settings.json` nem os hooks: isso é decisão do usuário.
