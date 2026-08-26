#!/usr/bin/env bash
# Local quality gate. It is a superset of the CI workflow: ruff, mypy, pytest and
# ciparity itself are the steps CI also runs, the rest catch problems before the push.
# Requires: uv (installs project tools), npx (markdownlint); gitleaks and lychee optional.
set -uo pipefail

FAILED=0
step() {
  local name="$1"
  shift
  echo "==> $name"
  if "$@"; then echo "OK"; else echo "FAILED: $name"; FAILED=1; fi
}

step "ruff format --check" uv run ruff format --check .
step "ruff check" uv run ruff check .
step "mypy --strict" uv run mypy
step "pytest" uv run python -m pytest -q
step "vulture" uv run vulture
step "ciparity on itself" uv run ciparity .
step "pip-audit" scripts/pip_audit.sh
step "markdownlint" npx -y markdownlint-cli2 "**/*.md"
if command -v gitleaks >/dev/null 2>&1; then
  step "gitleaks" gitleaks detect --source . --redact
else
  echo "==> gitleaks: SKIPPED (not installed)"
fi
if command -v lychee >/dev/null 2>&1; then
  step "lychee" lychee --no-progress --include-fragments README.md
else
  echo "==> lychee: SKIPPED (not installed)"
fi

exit $FAILED
