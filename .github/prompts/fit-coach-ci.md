You are running inside CI for repository personal-train-coach. Use facts only from `session.json` at the repo root plus paths explicitly mentioned below.

## Inputs (do not invent numbers)

- FIT source path committed/analyzed: `__FIT_PATH__`

## Files you MUST read before editing

1. `session.json` — structured parse output from `coach-parse --json`. Every numeric metric must trace to this file or explicitly stated as unknown/skip if absent.
2. `README.md` — keep the top matter unchanged (title, link to `repo-tutorial.md`, horizontal rule).

## Edit README.md

- Do not remove or rewrite `# personal-train-coach`, the line linking `repo-tutorial.md`, or the `---` separator above `## AI 教練分析報告`.
- Replace ONLY the body **under** `## AI 教練分析報告` down to (but not including) the next `## ` heading if present or EOF.
- Start that section with bullet or short line stating analyzed FIT file `__FIT_PATH__` and activity date/time if present in `session.json`.
- Write concise marathon-periodization coaching notes (aerobic base intensity distribution recovery weekly volume trend — if single session comment this session only plus general principles).
- Tone: professional actionable non-medical no diagnoses label uncertain inferences as assumptions.

## Write analysis file

- Create directory `analysis/` if missing.
- Write `analysis/__FIT_STEM__.md` with a fuller coaching narrative, still grounded in `session.json`; no fabricated metrics.

When done both files must exist on disk with saved changes.
