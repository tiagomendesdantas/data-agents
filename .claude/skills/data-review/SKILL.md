---
name: data-review
description: "Revisão somente leitura das alterações de dados (SQL, dbt, Python) pelo data-reviewer. Uso: /data-review [caminho | --staged | --all]."
argument-hint: "[caminho | --staged | --all]"
user-invocable: true
disable-model-invocation: true
context: fork
agent: data-reviewer
---

Revise as alterações de dados deste repositório. Escopo pedido: $ARGUMENTS (vazio significa tudo que está modificado ou não rastreado no git).

1. Liste o escopo com `git status --short` e `git diff --name-only`. Com `--staged`, use `git diff --cached --name-only`. Com um caminho, restrinja a ele. Com `--all`, inclua também os arquivos sem alteração em `sandbox/dbt/models`, `sandbox/dbt/tests` e `sandbox/pipelines`.
2. Leia cada arquivo no escopo e os yml e modelos upstream necessários para entender grain e contratos.
3. Rode as verificações somente leitura que fizerem sentido: `cd sandbox/dbt && uv run --project .. dbt parse --profiles-dir .`, `uv run --project sandbox ruff check sandbox`, `uv run --project sandbox pytest sandbox/tests -q`, e `dbt test --select <modelos alterados>`.
4. Aplique o checklist do seu prompt e entregue o veredito no formato exigido.

Não edite nenhum arquivo.
