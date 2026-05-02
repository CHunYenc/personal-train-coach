You are running inside CI for repository personal-train-coach. Use facts only from `session.json`, `sessions_summary.json`, and paths explicitly mentioned below.

## Inputs (do not invent numbers)

- FIT source path committed/analyzed: `__FIT_PATH__`

## Files you MUST read before editing

1. `session.json` — parse output for **this** FIT from `coach-parse --json`. Use for **`analysis/__FIT_STEM__.md`** (all single-file coaching depth: tables, optional Mermaid, narrative).
2. `sessions_summary.json` — built by `coach-sessions-summary` from **all** `data/*.fit`. Use for **`README.md`** history table rows only; each row includes precomputed `activity_window_utc8` and `table_*` strings (display timezone **Asia/Taipei / UTC+8**). Rebuild the README history table from `rows` only; do not invent columns or merge stale README numbers.
3. `README.md` — keep the top matter unchanged (title, link to `repo-tutorial.md`, horizontal rule).

## Role split

- **`README.md`** under `## AI 教練分析報告`: **historical index** (list + summary table + short pointer to the latest run). **No** per-session 現況摘要, **no** Mermaid charts, **no** long 教練建議 for the latest file here — those belong only in `analysis/*.md`.
- **`analysis/__FIT_STEM__.md`**: **single-file** coaching report for this activity (full structure as below).

## Edit README.md

- Do not remove or rewrite `# personal-train-coach`, the line linking `repo-tutorial.md`, or the `---` separator above `## AI 教練分析報告`.
- Replace ONLY the body **under** `## AI 教練分析報告` down to (but not including) the next `## ` heading if present or EOF.

### Required structure (under `## AI 教練分析報告`)

Use these **exact** `###` headings in this order:

1. **`### 歷史分析報告列表`** — Nested list linking each `analysis/<stem>.md`. **Grouping key** = first **6** characters of `<stem>`. Use `analysis/*.md` on disk; include every `*.md` under `analysis/`. **Ensure** `analysis/__FIT_STEM__.md` appears under the correct group. Remove a link only if that file no longer exists.

2. **`### 歷史詳細數據表`** — One markdown table. **Header row** must include **活動時間（UTC+8）** (not UTC). **Data**: recompute the table from **`sessions_summary.json`** field `rows` in file order (sorted basename); for each row use `fit_basename`, `activity_window_utc8`, `table_elapsed`, `table_distance`, `heart_rate_min_avg_max`, `speed_avg_max`, `table_calories`, `table_temp`, `table_ascent_descent`, `device`. If a cell field is empty in JSON, use `—` or leave consistent empty handling; do not guess.

3. **`### 解析來源`** — **Exactly 1–2 short lines**: state `__FIT_PATH__` is the file parsed this run, give the **UTC+8** activity window for that file (copy from the matching `sessions_summary.json` row’s `activity_window_utc8`, or derive consistently from `session.json` in Asia/Taipei), and link to detail: `` detailed analysis: [`analysis/__FIT_STEM__.md`](analysis/__FIT_STEM__.md) ``.

4. **`### 資料限制與免責`** — Brief bullets: history table is session-level summary from FIT parse; not medical advice; single-session depth and charts are in each `analysis/<stem>.md`.

Close with one line: **單次活動完整分析（表／圖／教練文字）見各 `analysis/<stem>.md`。**

Do **not** add `### 現況摘要`, `### 圖表`, or `### 教練建議` under README for the latest session.

## Write analysis file

- Create directory `analysis/` if missing.
- Write `analysis/__FIT_STEM__.md` as the **single-file** report, grounded in `session.json`.
- For human-readable activity start/end in the analysis doc, use **Asia/Taipei (UTC+8)** (e.g. match `activity_window_utc8` from `sessions_summary.json` for this stem, or convert `start_time` / `timestamp` the same way).
- Structure: at minimum `## 現況摘要` (markdown table(s); optional Mermaid aggregate chart from session fields), `## 教練建議`, then `## 補充觀點` or `## 細部說明` for longer context. Reiterate data limits / non-medical disclaimer once.
- No fabricated metrics.

When done both files must exist on disk with saved changes.
