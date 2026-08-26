#!/usr/bin/env bash
# Audit the dev dependency set. CI runs the same two commands as separate steps,
# so the pre-commit hook and the workflow stay in parity (ciparity checks this).
set -euo pipefail

REQ="${CIPARITY_REQ:-/tmp/ciparity-req.txt}"
uv export --no-emit-project --extra dev -o "$REQ" -q

if [ "$#" -eq 0 ]; then
  set -- --no-deps -r "$REQ"
fi
exec uv run pip-audit "$@"
