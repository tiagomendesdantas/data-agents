---
name: eda-protocol
description: "Protocolo para responder perguntas de negócio com dados: reformular a pergunta, consultar marts antes de staging antes de raw, validar números e responder com a query e os caveats. Use em análises, EDA e qualquer pergunta \"quanto\", \"qual\", \"por que\", \"compare\"."
---

# Protocolo de análise

## 1. Reformule a pergunta
Escreva em uma frase o que será medido, em que período, em que grain e com quais filtros. Se faltar algo essencial (período, métrica, segmento) e não houver padrão razoável, pergunte uma vez, em lote. Se puder assumir, assuma e declare.

## 2. Encontre a fonte certa
Ordem de preferência: marts (`fct_`, `dim_`, `mart_`), depois staging, por último raw. Leia o yml do modelo (`sandbox/dbt/models/**/*.yml`) para saber o grain e a definição da métrica. Se não existe modelo para a pergunta e a lógica em raw seria complexa ou frágil, responda com o que for seguro e registre "Próximo agente sugerido: analytics-engineer".

## 3. Explore antes de responder
- Contagens e faixas: `count(*)`, `min` e `max` da data, distintos das dimensões usadas.
- Confirme o grain: `group by chave having count(*) > 1`.
- Olhe nulos nas colunas que entram na métrica.

## 4. Responda com a query
Toda resposta numérica vem acompanhada da query que a gerou. Execute com `run_sql.py` (skill `stack-profile`) ou `make query`.

## 5. Valide
Pelo menos uma checagem independente: o total bate com outra agregação, reconcilia com um número conhecido, ou a ordem de grandeza faz sentido. Mostre a checagem.

## 6. Entregue
Arquivo `sandbox/analyses/YYYY-MM-DD_<slug>.md` a partir de `templates/analysis.md`: pergunta, fonte, SQL, resultado em tabela, validações, caveats (grain, filtros, dados faltantes, definição da métrica), próximos passos. Gráficos com matplotlib salvos ao lado como PNG quando ajudam, sempre com título, eixos nomeados e unidade.

## Nunca
- Responder número sem query.
- Usar `distinct` para "corrigir" duplicatas sem entender a causa.
- Alterar modelos dbt: isso é do analytics-engineer.
- Escrever fora de `sandbox/analyses/` e `sandbox/notebooks/`.
