---
name: ml-experiment
description: "Protocolo de experimento de ML: definição do alvo e da unidade de predição, baseline antes de qualquer modelo, split temporal, checagem de leakage, métricas com variância e registro reprodutível. Use em qualquer tarefa de modelagem preditiva ou experimento."
---

# Protocolo de experimento

## 0. Antes de treinar
- Alvo: o que está sendo previsto, em que unidade (linha de pedido, cliente-mês), em que horizonte.
- Dado disponível no momento da predição: para cada feature, ela existiria antes do evento? Se não, é leakage e sai.
- Métrica primária e por quê (PR-AUC em classes desbalanceadas, MAE em valores, etc.).

## 1. Baseline primeiro
Classe majoritária, média ou uma regra simples. Registre a métrica. Nenhum modelo é aceito sem bater o baseline.

## 2. Split
Temporal quando há tempo: treino até a data X, validação depois, teste separado da validação. Nunca aleatório em dados com tempo.

## 3. Modelo
Comece simples (regressão logística ou linear, árvore rasa). Só aumente complexidade com ganho medido. Seeds fixas. `Pipeline` do scikit-learn para que o pré-processamento não vaze.

## 4. Avaliação
Métrica primária e secundárias; variância (vários seeds ou validação cruzada temporal); erro por segmento; calibração quando a saída é probabilidade.

## 5. Registro
- Script reproduzível em `sandbox/ml/<slug>.py` (dados, features, split, treino, métricas), executável com `uv run --project sandbox python sandbox/ml/<slug>.py`.
- Notebook opcional em `sandbox/notebooks/` para exploração. O script é a fonte da verdade.
- Registro em `sandbox/experiments/YYYY-MM-DD_<slug>.md` a partir de `templates/experiment.md`.
- Features reutilizáveis em SQL: sugira um modelo dbt ao analytics-engineer em vez de duplicar lógica em pandas.

## Nunca
- Treinar sem baseline.
- Usar colunas pós-evento como feature.
- Reportar métrica de um único split sem variância.
- Ler o warehouse com conexão de escrita (use `read_only=True`).

Padrões de código e tabela de métricas: `reference.md`.
