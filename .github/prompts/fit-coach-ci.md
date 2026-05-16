You are running inside CI for repository personal-train-coach.

Use facts only from:
- `session.json`
- `__LLM_INPUT_PATH__`

## Inputs

- FIT source path committed/analyzed: `__FIT_PATH__`
- FIT stem for this run: `__FIT_STEM__`
- Compact context JSON path: `__LLM_INPUT_PATH__`

## Responsibilities

- `README.md` is rendered deterministically by `coach-render-readme`.
- **Do not edit `README.md`.**
- Write these two files only:
  1. `analysis/__FIT_STEM__.md`
  2. `coach_notes.md`

## Output 1: `analysis/__FIT_STEM__.md` (keep this file)

Write a Chinese single-session report mainly from `session.json`. You may use
goal/trend context from `__LLM_INPUT_PATH__` when needed.

Required structure:
1. `# YYYY/MM/DD HH:mm 跑步分析` (UTC+8, no raw filename in title)
2. `## 現況摘要`
3. `## 與目標的關係`
4. `## 教練建議`
5. `## 補充觀點`

Rules:
- no fabricated metrics
- in `## 現況摘要`, include a primary table with: 活動時間, 時長, 距離, 配速, 心率（低／均／高）, 卡路里, 裝置
- secondary table optional when fields exist
- mention non-medical / non-diagnostic boundary once in `## 補充觀點`
- if subjective data is absent in `__LLM_INPUT_PATH__`, clearly ask for RPE / enjoyment instead of guessing

## Output 2: `coach_notes.md` (now from llm_input only)

For this file, use only `__LLM_INPUT_PATH__`:
- `trend_context`
- `recent_history`
- `goal_context` (optional, only when directly relevant)

Do not read `sessions_summary.json` for this output.

Strict format:
- only bullet lines (`- ...`)
- 4–6 bullets total
- one line per bullet
- concise Chinese, factual, no long reasoning paragraphs
- no fabricated numbers
- no diagnosis
- include one data-scope-limit bullet and one non-medical disclaimer bullet

## Final checks

When done, both files must exist on disk:
- `analysis/__FIT_STEM__.md`
- `coach_notes.md`
