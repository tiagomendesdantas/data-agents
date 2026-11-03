# Entrypoint canônico do sandbox. Os agentes devem preferir estes alvos a comandos soltos.
SANDBOX  := sandbox
DBT_DIR  := $(SANDBOX)/dbt
UVRUN    := uv run --project $(SANDBOX)
export DUCKDB_PATH := $(abspath $(SANDBOX)/warehouse.duckdb)
export DBT_PROFILES_DIR := $(abspath $(DBT_DIR))
unexport VIRTUAL_ENV
DBT      := cd $(DBT_DIR) && uv run --project .. dbt

.PHONY: help setup seed dbt-build dbt-test dbt-docs query lint test sandbox clean

help: ## Lista os alvos
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup: ## Instala dependências do sandbox (uv sync)
	uv sync --project $(SANDBOX)

seed: ## Gera dados TPC-H (sf=0.1) no warehouse local; idempotente
	$(UVRUN) python $(SANDBOX)/seed.py

dbt-build: ## dbt build (modelos + testes)
	$(DBT) build

dbt-test: ## dbt test
	$(DBT) test

dbt-docs: ## Gera docs do dbt em sandbox/dbt/target
	$(DBT) docs generate

query: ## Executa SQL no warehouse: make query q="select 1"
	$(UVRUN) python .claude/skills/stack-profile/scripts/run_sql.py "$(q)"

lint: ## ruff (Python) + sqlfluff (SQL dos modelos)
	$(UVRUN) ruff check $(SANDBOX) .claude
	cd $(DBT_DIR) && uv run --project .. sqlfluff lint models tests

test: ## pytest do sandbox
	$(UVRUN) pytest $(SANDBOX)/tests

sandbox: setup seed dbt-build ## Setup completo: deps + seed + dbt build

clean: ## Remove artefatos do dbt (não apaga o warehouse)
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/logs $(DBT_DIR)/dbt_packages
