#!/usr/bin/env bash
# Hook SessionStart: mostra o ambiente ativo e avisa se o sandbox não foi semeado.
root="${CLAUDE_PROJECT_DIR:-$PWD}"
stack="$root/.claude/skills/stack-profile/stack.toml"
env_name=$(python3 -c 'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb"))["env"]["name"])' "$stack" 2>/dev/null || echo "desconhecido")
msg="[data-agents] stack.toml env.name=$env_name."
if [ ! -f "$root/sandbox/warehouse.duckdb" ]; then
  msg="$msg Warehouse local ausente: rode \`make sandbox\` antes de usar os agentes."
fi
echo "$msg"
