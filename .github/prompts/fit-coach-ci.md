You are running inside CI for repository personal-train-coach.

Use facts only from:
- `session.json`
- `sessions_summary.json`
- `training_profile.json` (if present)
- `training_journal/*.json` (if present)

## Inputs

- FIT source path committed/analyzed: `__FIT_PATH__`
- FIT stem for this run: `__FIT_STEM__`

## Important change in responsibilities

- `README.md` is now rendered deterministically by `coach-render-readme`.
- **Do not edit `README.md`.**
- Your job in CI is now:
  1. Write `analysis/__FIT_STEM__.md` (single-session deep report)
  2. Write `coach_notes.md` (cross-session short bullets for README section `### 看完歷史詳細數據後的教練小提醒：`)

## Output 1: `analysis/__FIT_STEM__.md`

Write a Chinese single-session report grounded in `session.json`.

Required structure:
1. `# YYYY/MM/DD HH:mm 跑步分析` (UTC+8; no raw filename in title)
2. `## 現況摘要`
3. `## 與目標的關係`
4. `## 教練建議`
5. `## 補充觀點`

Rules:
- All numbers must come from JSON files; no fabricated metrics.
- In `## 現況摘要`, include a primary table with: 活動時間, 時長, 距離, 配速, 心率（低／均／高）, 卡路里, 裝置.
- Secondary table is optional (only when fields exist).
- Mermaid is optional and only when it adds real information.
- Mention non-medical / non-diagnostic boundary once in `## 補充觀點`.
- If subjective journal data is missing, explicitly ask for RPE / enjoyment instead of guessing.

## Output 2: `coach_notes.md`

Write concise bullets for README's coaching reminder section.

Strict format:
- File must contain **only** bullet lines (`- ...`), no headings, no preface text.
- 4–6 bullets total.
- Each bullet must be one line.
- Use only facts from `sessions_summary.json` historical rows.
- No fabricated numbers.
- No diagnosis.
- Include one bullet on data scope limits and one brief non-medical disclaimer.

Style for `coach_notes.md`:
- concise, factual, Chinese
- no long reasoning paragraphs
- no semicolon chains

## Final checks

When done, both files must exist on disk:
- `analysis/__FIT_STEM__.md`
- `coach_notes.md`
