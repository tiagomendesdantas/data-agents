# <Nome do experimento>

**Data:** YYYY-MM-DD
**Script:** `sandbox/ml/<slug>.py`
**Hipótese:** <o que esperamos e por quê>

## Problema
- Alvo: ...
- Unidade de predição: ...
- Horizonte: ...
- Métrica primária: ... (por quê)

## Dados
- Fonte: `marts.<modelo>` (grain conforme yml)
- Período: ...
- Linhas: treino N / validação N / teste N
- Split: temporal, cutoff em ...

## Features
| feature | disponível antes do evento? | observação |
|---|---|---|
| ... | sim | ... |

## Resultados
| modelo | métrica primária | secundárias | seeds |
|---|---|---|---|
| baseline | ... | ... | n/a |
| modelo 1 | ... | ... | 5 |

## Análise de erro
- <por segmento, calibração, casos extremos>

## Decisão
- <seguir / descartar / iterar> e por quê

## Próximos passos
- ...
