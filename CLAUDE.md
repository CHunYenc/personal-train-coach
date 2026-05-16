# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Parse a FIT/TCX file (human-readable)
uv run coach-parse [path/to/file.fit]

# Parse with JSON output (used by CI)
uv run coach-parse --json [path/to/file.fit]

# Parse the latest file in data/ (auto-detected by mtime)
uv run coach-parse

# Build cross-session summary (writes sessions_summary.json)
uv run coach-sessions-summary
```

There is no test suite or linter configured.

## Architecture

This is a **personal running training log analyzer**. It parses Garmin/COROS activity files and generates AI-powered coaching reports in Chinese.

### Data flow

```
data/*.fit or data/*.tcx
    ↓ coach-parse --json
session.json
data/*.fit or data/*.tcx + training_profile.json + training_journal/*.json
    ↓ coach-sessions-summary
sessions_summary.json
    ↓ Cursor Agent (CI)
analysis/<stem>.md + README.md update
```

### Key modules

- **`ptc/cli.py`** — Parses binary `.fit` (via `fitdecode`) and XML `.tcx` files. Extracts session-level aggregates: distance, time, pace, heart rate, calories, ascent. `parse_fit()` reads `file_id` + final `session` frame; `parse_tcx()` reads XML equivalents.

- **`ptc/build_sessions_summary.py`** — Scans all `data/*.fit` and `data/*.tcx`, builds a chronologically-sorted array of rows with precomputed display strings (table_elapsed_hms, table_distance_km, table_pace, etc.). Also includes `training_profile.json`, optional `training_journal/*.json` entries, weekly trends, and 10K goal progress when available. All datetimes are rendered in Asia/Taipei (UTC+8). Writes `sessions_summary.json`.

- **`training_profile.json`** — Versioned goal context for reports: target race, emotional goal, long-term speed memory, and reporting preferences.

- **`training_journal/`** — Optional post-run subjective JSON logs keyed by activity stem (RPE, enjoyment, sleep, soreness, notes).

### CI pipeline (`.github/workflows/fit-parse.yml`)

Triggered on push to `main` when `data/**` changes. Four jobs in sequence:
1. **Parse** — runs `coach-parse --json`, uploads `session.json` artifact
2. **Build summary** — runs `coach-sessions-summary`, uploads `sessions_summary.json` artifact
3. **Cursor Agent** — calls Cursor CLI with prompt from `.github/prompts/fit-coach-ci.md`; writes `analysis/<stem>.md` and updates `README.md`
4. **Commit & push** — commits generated files back to the branch

The CI requires a `CURSOR_API_KEY` secret. File selection uses `git diff-tree` (not mtime) for determinism.

### AI coaching output

- **`analysis/<stem>.md`** — Per-activity coaching report in Chinese
- **`README.md`** `## AI 教練分析報告` section — auto-maintained goal dashboard + weekly trends + summary table + report links

The prompt template at `.github/prompts/fit-coach-ci.md` strictly controls output structure and language. Do not fabricate numbers; all metrics must come from JSON artifacts.

### Cursor rules

- `.cursor/rules/karpathy-guidelines.mdc` — Think before coding; surface assumptions
- `.cursor/rules/running_coach_behavioral_guidelines-v2.mdc` — Data-driven caution, recovery prioritization, acknowledge uncertainty
- `.cursor/skills/ai-marathon-coach/SKILL.md` — Custom skill: reads latest `.fit`, runs parse, regenerates README + analysis in Chinese

### Timezone

All datetime display is Asia/Taipei (UTC+8). The `_coerce_datetime()` and `_to_utc8_label()` helpers in `build_sessions_summary.py` handle ISO 8601 + Z-suffix parsing and formatting.
