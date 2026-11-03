#!/usr/bin/env python3
"""Executa SQL no warehouse descrito em stack.toml.

Uso:
  run_sql.py "select 1"
  run_sql.py --file consulta.sql
  run_sql.py "select * from marts.fct_orders" --limit 20 --csv
  run_sql.py "create table x as select 1" --write

Somente leitura por padrão. Se o DuckDB estiver travado por outro processo, tenta de novo por ~10 s.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # .claude/skills/stack-profile/scripts -> raiz do repo
STACK = ROOT / ".claude/skills/stack-profile/stack.toml"


def load_stack() -> dict:
    return tomllib.loads(STACK.read_text(encoding="utf-8"))


def connect_duckdb(cfg: dict, write: bool):
    import duckdb

    path = ROOT / cfg["warehouse"]["path"]
    if not path.exists():
        sys.exit(f"warehouse não encontrado em {path}; rode `make seed`.")
    delay = 0.5
    for attempt in range(8):
        try:
            return duckdb.connect(str(path), read_only=not write)
        except duckdb.IOException as exc:
            if "lock" not in str(exc).lower() or attempt == 7:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 3.0)
    raise RuntimeError("unreachable")


def print_table(columns: list[str], rows: list[tuple]) -> None:
    cells = [[("" if v is None else str(v)) for v in row] for row in rows]
    widths = [len(c) for c in columns]
    for row in cells:
        for i, v in enumerate(row):
            widths[i] = min(max(widths[i], len(v)), 60)
    fmt = " | ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*[c[:60] for c in columns]))
    print("-+-".join("-" * w for w in widths))
    for row in cells:
        print(fmt.format(*[v[:60] for v in row]))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("sql", nargs="?", help="SQL a executar")
    parser.add_argument("--file", help="arquivo .sql a executar (alternativa ao argumento)")
    parser.add_argument(
        "--limit", type=int, default=50, help="máximo de linhas exibidas (padrão 50)"
    )
    parser.add_argument("--csv", action="store_true", help="saída em CSV")
    parser.add_argument(
        "--write", action="store_true", help="abre o warehouse com permissão de escrita"
    )
    args = parser.parse_args()

    sql = Path(args.file).read_text(encoding="utf-8") if args.file else args.sql
    if not sql or not sql.strip():
        parser.error("informe o SQL como argumento ou via --file")

    cfg = load_stack()
    wtype = cfg["warehouse"]["type"]
    if wtype != "duckdb":
        sys.exit(
            f"warehouse.type={wtype!r} ainda não é suportado por run_sql.py; adicione um conector."
        )

    con = connect_duckdb(cfg, args.write)
    try:
        con.execute(sql)
        if con.description is None:
            print("OK (sem linhas de resultado)")
            return 0
        columns = [d[0] for d in con.description]
        rows = con.fetchmany(args.limit + 1)
        truncated = len(rows) > args.limit
        rows = rows[: args.limit]
        if args.csv:
            writer = csv.writer(sys.stdout)
            writer.writerow(columns)
            writer.writerows(rows)
        else:
            print_table(columns, rows)
            print(f"\n{len(rows)} linha(s){' (truncado; use --limit)' if truncated else ''}")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
