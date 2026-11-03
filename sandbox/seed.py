#!/usr/bin/env python3
"""Semeia o warehouse local do sandbox com dados TPC-H.

Idempotente: se raw.orders já existe, não faz nada (use --force para regenerar).
Uso: uv run --project sandbox python sandbox/seed.py [--force] [--sf 0.1]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "warehouse.duckdb"
TABLES = ["region", "nation", "supplier", "part", "partsupp", "customer", "orders", "lineitem"]


def table_exists(con: duckdb.DuckDBPyConnection, schema: str, table: str) -> bool:
    row = con.execute(
        "select count(*) from information_schema.tables where table_schema = ? and table_name = ?",
        [schema, table],
    ).fetchone()
    return bool(row and row[0])


def generate(con: duckdb.DuckDBPyConnection, sf: float) -> None:
    con.execute("INSTALL tpch; LOAD tpch;")
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    for t in TABLES:
        con.execute(f"DROP TABLE IF EXISTS raw.{t};")
    try:
        con.execute(f"CALL dbgen(sf={sf}, schema='raw');")
    except duckdb.Error as exc:  # versões antigas do tpch não aceitam schema=
        print(f"dbgen(schema='raw') não suportado ({exc}); gerando em main e copiando.")
        for t in TABLES:
            con.execute(f"DROP TABLE IF EXISTS main.{t};")
        con.execute(f"CALL dbgen(sf={sf});")
        for t in TABLES:
            con.execute(f"CREATE TABLE raw.{t} AS SELECT * FROM main.{t};")
            con.execute(f"DROP TABLE main.{t};")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="regenera mesmo se raw.orders existir")
    parser.add_argument("--sf", type=float, default=0.1, help="scale factor do TPC-H (padrão 0.1)")
    args = parser.parse_args()

    con = duckdb.connect(str(DB_PATH))
    if table_exists(con, "raw", "orders") and not args.force:
        print(f"raw.orders já existe em {DB_PATH}; nada a fazer (use --force para regenerar).")
    else:
        print(f"Gerando TPC-H sf={args.sf} em {DB_PATH} ...")
        generate(con, args.sf)
    for t in TABLES:
        (n,) = con.execute(f"select count(*) from raw.{t}").fetchone()
        print(f"raw.{t:<10} {n:>10,}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
