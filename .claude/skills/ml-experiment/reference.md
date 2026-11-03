# Referência de experimentos

## Ler dados do sandbox
```python
import duckdb, tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # sandbox/ml/x.py -> raiz
cfg = tomllib.loads((ROOT / ".claude/skills/stack-profile/stack.toml").read_text())
con = duckdb.connect(str(ROOT / cfg["warehouse"]["path"]), read_only=True)
df = con.execute("select ... from marts.fct_orders").df()
```

## Esqueleto do script
```python
SEED = 42
# 1. carregar e definir alvo
# 2. split temporal: cutoff = data; train = antes, valid = depois
# 3. baseline: DummyClassifier(strategy="most_frequent") / DummyRegressor(strategy="mean")
# 4. modelo: Pipeline([("prep", ColumnTransformer(...)), ("model", LogisticRegression(...))])
# 5. métricas em valid (e em test só no final), várias seeds quando o modelo é estocástico
# 6. imprimir tabela baseline vs modelo e salvar em sandbox/experiments/<data>_<slug>_metrics.csv
```

## Métricas
| Problema | Primária | Secundárias |
|---|---|---|
| Classificação desbalanceada | PR-AUC | ROC-AUC, recall em precisão fixa, Brier |
| Classificação balanceada | ROC-AUC ou F1 | acurácia, matriz de confusão |
| Regressão de valor | MAE | RMSE, MAPE (cuidado com zeros), erro por faixa |
| Ranking | NDCG@k | MAP@k |

## Checklist de leakage
- Feature derivada do alvo ou de evento posterior (ex.: `receipt_date` para prever atraso).
- Agregações que incluem o período de validação.
- Pré-processamento ajustado no dataset inteiro (scaler, encoder) em vez de só no treino.
- Duplicatas da mesma entidade em treino e validação.

## Exemplo de alvo no sandbox
"Linha de pedido atrasada" = `is_late` em `stg_tpch__line_items`. Features válidas no momento do pedido: `ship_mode`, `quantity`, `discount`, `order_priority`, mês do pedido, região do cliente. Inválidas: `receipt_date`, `ship_date` após o cutoff.
