#!/usr/bin/env python3
"""Hook PreToolUse (Bash): bloqueia SQL destrutivo fora do sandbox.

Lê o JSON do hook no stdin. Só age quando o comando invoca um cliente SQL
(duckdb, psql, bq, snowsql, dbt run-operation, run_sql.py, ...) ou `dbt run/build --full-refresh`.
Se `env.name == "sandbox"` em stack.toml, libera duckdb, dbt e run_sql.py.
Fora do sandbox: DROP SCHEMA/DATABASE e TRUNCATE são negados; o resto pede confirmação.

Limites conhecidos: não vê SQL montado dinamicamente (python -c), nem palavra-chave dentro
de string literal. É cinto de segurança, não cerca.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tomllib
from pathlib import Path

CLIENT_RE = re.compile(
    r"\b(duckdb|psql|pgcli|mysql|bq\s+query|snowsql|snow\s+sql|clickhouse-client|sqlite3"
    r"|dbt\s+run-operation|run_sql\.py)\b",
    re.I,
)
FULL_REFRESH_RE = re.compile(r"\bdbt\s+(run|build)\b.*--full-refresh", re.I | re.S)
SANDBOX_CLIENT_RE = re.compile(r"\b(duckdb|dbt|run_sql\.py)\b", re.I)
REAL_ONLY_CLIENT_RE = re.compile(
    r"\b(psql|pgcli|mysql|bq\s+query|snowsql|snow\s+sql|clickhouse-client)\b", re.I
)
FILE_ARG_RE = re.compile(r"(?:\s-f\s+|\s<\s*|--file[= ]\s*)([\w./~-]+\.sql)\b")

HARD = [
    ("DROP SCHEMA/DATABASE", re.compile(r"\bdrop\s+(schema|database)\b", re.I)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.I)),
]
SOFT = [
    ("DROP TABLE/VIEW", re.compile(r"\bdrop\s+(table|view|materialized\s+view)\b", re.I)),
    ("ALTER TABLE ... DROP", re.compile(r"\balter\s+table\b.*\bdrop\b", re.I | re.S)),
]
DELETE_RE = re.compile(r"\bdelete\s+from\b", re.I)
UPDATE_RE = re.compile(r"\bupdate\s+[\w.\"`]+\s+set\b", re.I)
WHERE_RE = re.compile(r"\bwhere\b", re.I)


def project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env) if env else Path(__file__).resolve().parents[2]


def env_name(root: Path) -> str:
    try:
        cfg = tomllib.loads((root / ".claude/skills/stack-profile/stack.toml").read_text("utf-8"))
        return str(cfg.get("env", {}).get("name", "")).strip().lower()
    except Exception:  # stack.toml ausente ou inválido: trate como ambiente real
        return ""


def strip_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return sql


def payload(command: str, root: Path) -> str:
    parts = [command]
    for match in FILE_ARG_RE.finditer(command):
        candidate = Path(os.path.expanduser(match.group(1)))
        if not candidate.is_absolute():
            candidate = root / candidate
        try:
            if candidate.resolve().is_relative_to(root.resolve()) and candidate.is_file():
                parts.append(candidate.read_text("utf-8", errors="ignore"))
        except OSError:
            pass
    return strip_comments("\n".join(parts))


def findings(text: str, command: str) -> tuple[list[str], list[str]]:
    hard: list[str] = []
    soft: list[str] = []
    for stmt in re.split(r";", text):
        stmt = stmt.strip()
        if not stmt:
            continue
        for label, rx in HARD:
            if rx.search(stmt):
                hard.append(label)
        for label, rx in SOFT:
            if rx.search(stmt):
                soft.append(label)
        if DELETE_RE.search(stmt) and not WHERE_RE.search(stmt):
            soft.append("DELETE sem WHERE")
        if UPDATE_RE.search(stmt) and not WHERE_RE.search(stmt):
            soft.append("UPDATE sem WHERE")
    if FULL_REFRESH_RE.search(command):  # no comando cru: strip_comments removeria o '--'
        soft.append("dbt --full-refresh")
    return sorted(set(hard)), sorted(set(soft))


def decide(decision: str, reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    command = str(data.get("tool_input", {}).get("command", ""))
    if not (CLIENT_RE.search(command) or FULL_REFRESH_RE.search(command)):
        sys.exit(0)

    root = project_root()
    text = payload(command, root)
    hard, soft = findings(text, command)
    if not hard and not soft:
        sys.exit(0)

    is_sandbox = env_name(root) == "sandbox"
    uses_real_client = bool(REAL_ONLY_CLIENT_RE.search(command))
    if is_sandbox and not uses_real_client and SANDBOX_CLIENT_RE.search(command):
        sys.exit(0)  # sandbox local: liberado

    found = ", ".join(hard + soft)
    where = "ambiente real" if not is_sandbox else "cliente de warehouse externo"
    if hard:
        decide(
            "deny",
            f"[sql_guard] {found} bloqueado em {where}. Edite stack.toml ou peça ao usuário.",
        )
    decide(
        "ask", f"[sql_guard] Operação destrutiva ({found}) em {where}. Confirme antes de executar."
    )


if __name__ == "__main__":
    main()
