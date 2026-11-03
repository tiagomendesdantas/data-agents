"""Smoke test do sandbox: o warehouse existe e os dados TPC-H foram semeados."""

from pathlib import Path

import duckdb
import pytest

WAREHOUSE = Path(__file__).resolve().parents[1] / "warehouse.duckdb"


@pytest.fixture(scope="module")
def con():
    if not WAREHOUSE.exists():
        pytest.skip("warehouse.duckdb não existe; rode `make seed`")
    connection = duckdb.connect(str(WAREHOUSE), read_only=True)
    yield connection
    connection.close()


def test_raw_orders_row_count(con):
    (n,) = con.execute("select count(*) from raw.orders").fetchone()
    assert n == 150_000


def test_raw_tables_exist(con):
    rows = con.execute(
        "select table_name from information_schema.tables where table_schema = 'raw' order by 1"
    ).fetchall()
    names = {r[0] for r in rows}
    assert {"customer", "orders", "lineitem", "nation", "region"} <= names
