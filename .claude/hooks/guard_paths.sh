#!/usr/bin/env bash
# Hook PreToolUse (Write|Edit|NotebookEdit) para agentes com escrita restrita.
# Uso: guard_paths.sh <prefixo-permitido> [<prefixo-permitido> ...]   (prefixos relativos à raiz do projeto)
# Sai 0 se o arquivo está sob um dos prefixos; sai 2 (bloqueia) caso contrário.
set -euo pipefail

input=$(cat)
file=$(printf '%s' "$input" | python3 -c '
import json, sys
d = json.load(sys.stdin)
t = d.get("tool_input", {})
print(t.get("file_path") or t.get("notebook_path") or "")
')
[ -z "$file" ] && exit 0

root="${CLAUDE_PROJECT_DIR:-$PWD}"
case "$file" in
  "$root"/*) rel="${file#"$root"/}" ;;
  /*)        rel="$file" ;;
  *)         rel="$file" ;;
esac

for prefix in "$@"; do
  case "$rel" in
    "$prefix"|"$prefix"/*) exit 0 ;;
  esac
done

echo "[guard_paths] Este agente só escreve em: $* (tentou: $rel)." >&2
exit 2
