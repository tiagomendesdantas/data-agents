#!/usr/bin/env python3
"""Perfila uma tabela do warehouse descrito em stack.toml (somente leitura).

Uso: profile_table.py <schema.tabela> [--top 5]
Saída: linhas; por coluna: tipo, % nulos, distintos, min, max, top valores.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # .claude/skills/data-quality-checks/scripts -> raiz
STACK = ROOT / ".claude/skills/stack-profile/stack.toml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", help="schema.tabela, ex.: marts.fct_orders")
    parser.add_argument(
        "--top", type=int, default=5, help="quantos valores mais frequentes mostrar"
    )
    args = parser.parse_args()

    if "." not in args.table:
        sys.exit("informe schema.tabela")
    schema, table = args.table.split(".", 1)

    cfg = tomllib.loads(STACK.read_text(encoding="utf-8"))
    if cfg["warehouse"]["type"] != "duckdb":
        sys.exit("profile_table.py só suporta duckdb por enquanto.")

    import duckdb

    path = ROOT / cfg["warehouse"]["path"]
    if not path.exists():
        sys.exit(f"warehouse não encontrado em {path}; rode `make seed`.")
    con = duckdb.connect(str(path), read_only=True)

    cols = con.execute(
        "select column_name, data_type from information_schema.columns "
        "where table_schema = ? and table_name = ? order by ordinal_position",
        [schema, table],
    ).fetchall()
    if not cols:
        sys.exit(f"tabela {args.table} não encontrada")

    fq = f'"{schema}"."{table}"'
    (n,) = con.execute(f"select count(*) from {fq}").fetchone()
    print(f"{args.table}: {n:,} linhas, {len(cols)} colunas\n")

    for name, dtype in cols:
        q = f'"{name}"'
        nulls, distinct = con.execute(
            f"select count(*) - count({q}), count(distinct {q}) from {fq}"
        ).fetchone()
        try:
            mn, mx = con.execute(f"select min({q}), max({q}) from {fq}").fetchone()
        except duckdb.Error:
            mn, mx = "n/a", "n/a"
        top = con.execute(
            f"select {q}, count(*) as c from {fq} "
            f"group by 1 order by c desc nulls last limit {args.top}"
        ).fetchall()
        pct = (100.0 * nulls / n) if n else 0.0
        tops = ", ".join(f"{v!r} x{c:,}" for v, c in top)
        print(
            f"- {name} ({dtype}): nulos {pct:.1f}%, distintos {distinct:,}, min {mn!r}, max {mx!r}"
        )
        print(f"    top: {tops}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
