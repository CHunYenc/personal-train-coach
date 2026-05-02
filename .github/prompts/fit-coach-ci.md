You are running inside CI for repository personal-train-coach. Use facts only from `session.json` at the repo root plus paths explicitly mentioned below.

## Inputs (do not invent numbers)

- FIT source path committed/analyzed: `__FIT_PATH__`

## Files you MUST read before editing

1. `session.json` — structured parse output from `coach-parse --json`. Every numeric metric must trace to this file or explicitly stated as unknown/skip if absent.
2. `README.md` — keep the top matter unchanged (title, link to `repo-tutorial.md`, horizontal rule).

## Edit README.md

- Do not remove or rewrite `# personal-train-coach`, the line linking `repo-tutorial.md`, or the `---` separator above `## AI 教練分析報告`.
- Replace ONLY the body **under** `## AI 教練分析報告` down to (but not including) the next `## ` heading if present or EOF.

### Required structure (under `## AI 教練分析報告`)

Use these **exact** `###` headings in this order (so the section stays scannable):

1. **`### 歷史分析報告列表`** — Nested list of links to `analysis/<stem>.md`. **Grouping key** = first **6** characters of `<stem>` (e.g. stem `20260418173835` → group `202604`). Before editing, inspect `README.md` and `analysis/*.md` on disk: **keep** existing stems and links; **ensure** `analysis/__FIT_STEM__.md` is listed under the correct group (add group bullet if missing). **Do not** drop other sessions’ links unless their file is gone from the repo.

2. **`### 歷史詳細數據表`** — One GitHub markdown **table** with columns like: 檔案, 活動時間（UTC）, 經過時間／計時, 距離, 心率（低／均／高）, 速度（均／高）, 卡路里, 均溫（感測）, 爬升／下降, 裝置. **Merge rule**: copy existing **non-current** rows from the prior README verbatim (CI only has `session.json` for **this** FIT). **Insert or replace** the row for `basename(__FIT_PATH__)` using **only** `session.json` for that file; omit sub-columns if keys are missing, do not invent.

3. **`### 解析來源`** — One short line: analyzed file path `__FIT_PATH__`, activity window from `session.json` (`start_time` → `timestamp`, state timezone, usually UTC).

4. **`### 現況摘要`** — At least **one GitHub-flavored markdown table** summarizing key fields present in `session.json` (e.g. sport, elapsed/timer, distance, pace if derivable from distance+time without new tools, heart rate min/avg/max, speed avg/max, calories, temperature, ascent/descent, device from `file_id` if present). Omit table rows for keys that are missing; do not fabricate.

5. **`### 圖表`** — Optional but **preferred when the data supports a honest aggregate chart**:
   - `session.json` has **no per-second time series**; do **not** imply intra-workout curves.
   - Allowed: **Mermaid `xychart-beta`** (or other Mermaid supported on GitHub) using **only** numbers copied from `session.json`, e.g. heart rate `[min_heart_rate, avg_heart_rate, max_heart_rate]` as a bar chart when all three exist. If a sensible aggregate chart would mislead (e.g. only one speed value), write one line: 「本筆 `session.json` 僅有彙總欄位，無逐筆紀錄，故不繪製時間序列圖；若需折線圖需擴充解析輸出。」 and skip the code block.
   - If you include Mermaid, keep the chart title/axis labels readable (Chinese or short English).

6. **`### 教練建議`** — Short **bullet list** (marathon periodization angle, recovery, intensity distribution limits, what is unknown from this file). Professional, actionable, **non-medical**, no diagnoses; label uncertain inferences as assumptions.

7. **`### 資料限制與免責`** — Brief bullets: single-session limits, no zone breakdown if not in JSON, not medical advice, link to fuller file below.

End with one line: `更完整敘事見 analysis/__FIT_STEM__.md` (use the real stem, i.e. `__FIT_STEM__` replaced by the basename of the FIT without `.fit`).

## Write analysis file

- Create directory `analysis/` if missing.
- Write `analysis/__FIT_STEM__.md` with a fuller narrative, still grounded in `session.json`.
- Use clear structure: at minimum `## 現況摘要` (include the same or richer **markdown table(s)** as README; optional same Mermaid aggregate chart), then `## 教練建議` (actionable bullets + short paragraphs as needed), then `## 細部說明` or `## 補充觀點` for longer coaching context. Reiterate data limits / non-medical disclaimer once.
- No fabricated metrics.

When done both files must exist on disk with saved changes.
