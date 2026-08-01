# Contributing

Thanks for improving `ciparity`.

1. Keep the parser static: no network calls, no Docker, and it never runs the tools it compares.
2. A new CI provider is a new module in `src/ciparity/ci/` plus fixtures under `tests/fixtures/`.
3. Every new finding needs a fixture and a test that fails without the change.
4. Unparsed input is a blind spot and must be reported, never skipped silently.
5. Run `bash scripts/check.sh` before opening a PR. It is the same list CI runs.
6. If you change terminal output, regenerate the README demo with
   `uv run python scripts/demo_gif.py`. The GIF is recorded from real runs, never drawn by hand.
