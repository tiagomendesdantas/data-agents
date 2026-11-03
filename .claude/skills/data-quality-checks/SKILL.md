---
name: data-quality-checks
description: "Catálogo de testes de dados (unicidade, nulos, relacionamentos, valores aceitos, volume, freshness, anomalias), contratos de schema e rubrica de classificação de PII. Use ao adicionar testes, avaliar cobertura ou classificar colunas sensíveis."
---

# Checks de qualidade

## Princípio
Teste o que a evidência mostra, não palpite. Perfile a tabela antes de propor um teste:
```
uv run --project sandbox python .claude/skills/data-quality-checks/scripts/profile_table.py marts.fct_orders
```
Saída: contagem de linhas e, por coluna, tipo, % de nulos, distintos, min, max e top valores.

## Catálogo: o que usar e quando
| Risco | Teste | Onde |
|---|---|---|
| Chave duplicada | `unique` + `not_null` na PK | todo modelo |
| Grain composto duplicado | teste singular com `group by ... having count(*) > 1` | modelos com chave composta |
| FK órfã | `relationships` | toda FK em marts |
| Enum inválido | `accepted_values` | colunas de status e categoria |
| Métrica impossível | teste singular (`where net_revenue < 0`) | marts |
| Volume anormal | teste singular comparando `count(*)` com o upstream ou com uma faixa | marts críticos |
| Freshness | `freshness` na source com `loaded_at_field` | sources com carga contínua |
| Contrato de schema | `contract: {enforced: true}` + `data_type` por coluna | marts consumidos por BI ou ML |

Todo teste novo deve:
1. Falhar em um caso ruim conhecido. Mostre como: inverta o `where` ou insira um registro ruim em uma tabela temporária do sandbox e rode o teste contra ela.
2. Passar nos dados atuais.
3. Ter o motivo registrado (comentário na primeira linha do teste singular ou `description` no yml).

Não crie thresholds sem justificativa numérica vinda do profile.

## Freshness no sandbox
Os dados TPC-H são estáticos (1992 a 1998). Nunca compare com `now()`. Compare contra `max(order_date)` do próprio dataset ou pule freshness no sandbox e documente a decisão.

## Rubrica de PII
| Classe | Exemplos | Marcação no yml |
|---|---|---|
| Direta | nome, e-mail, telefone, CPF, endereço | `meta: {pii: true, pii_class: direct}` |
| Indireta | data de nascimento, CEP, IP, id de dispositivo | `meta: {pii: true, pii_class: indirect}` |
| Sensível | saúde, religião, dados financeiros pessoais | `meta: {pii: true, pii_class: sensitive}` |
| Não PII | chaves técnicas, métricas agregadas | nada |

Dados sintéticos (TPC-H) são classificados como se fossem reais: a convenção vale para quando a stack for trocada.

Exemplos completos de yml e testes singulares: `reference.md`.
