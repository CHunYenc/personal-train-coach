# AGENTS.md

This repo is a personal running-coach data pipeline (Python 3.13 + `uv`). For the full product overview, data flow, module map, and the canonical dev commands, read `CLAUDE.md` — it is the source of truth and is written in Traditional Chinese.

## Cursor Cloud specific instructions

- Runtime/deps: Python 3.13 (pinned in `.python-version`) is managed by `uv`; `uv sync` provisions the interpreter and the single dependency (`fitdecode`). `uv` is preinstalled on the VM and resolves on `PATH` in login and non-login shells.
- No test suite and no linter exist (see `CLAUDE.md`). "Testing end-to-end" means running the `uv run coach-*` CLIs against the sample files in `data/` and checking the JSON/Markdown outputs. There is no server/GUI — this is a terminal-only pipeline.
- Canonical commands are documented in `CLAUDE.md` (`coach-parse`, `coach-sessions-summary`, `coach-build-llm-input`, `coach-render-readme`). Don't duplicate them here.
- Benign noise: parsing COROS `.fit` files prints `fitdecode` `UserWarning: invalid field size ...` to stderr. This is expected and does not indicate failure.
- Side effects to be aware of before committing: `coach-render-readme` rewrites the `## AI 教練分析報告` section of `README.md` in place. `sessions_summary.json` is git-ignored, but `README.md` is tracked — `git checkout -- README.md` if you ran the renderer only for testing.
- The LLM report step (Cursor Agent producing `analysis/<stem>.md` + `coach_notes.md`) is optional locally and requires the Cursor CLI plus a `CURSOR_API_KEY` secret; it is only wired up in CI (`.github/workflows/fit-parse.yml`). The deterministic Python pipeline runs fully without it.
