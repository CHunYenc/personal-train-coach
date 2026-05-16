# personal-train-coach — 使用教學

個人跑步／馬拉松訓練用專案：用 **uv** 管理 Python 環境，解析 Garmin **`.fit`** 活動檔並輸出摘要（距離、時間、配速、心率等）。

## 需求

- [Python](https://www.python.org/downloads/) **3.13+**（與 `pyproject.toml` 中 `requires-python` 一致）
- [uv](https://docs.astral.sh/uv/getting-started/installation/)（用來安裝依賴與執行程式）

## 安裝

在專案根目錄執行：

```bash
uv sync
```

會建立 `.venv`、安裝 `fitdecode` 與本專案（含指令 `coach-parse`）。

## 使用方式

將 `.fit` 放在 `data/` 底下。

### 解析「最新」的 `data/*.fit`

以檔案修改時間（mtime）決定最新檔：

```bash
uv run coach-parse
```

等同於：

```bash
uv run python main.py
```

### 指定檔案

```bash
uv run coach-parse "data/基礎有氧跑20260501174139.fit"
```

### JSON 輸出（給腳本或後續 AI 流程用）

```bash
uv run coach-parse --json
uv run coach-parse "data/你的檔案.fit" --json
```

### 跨場次摘要（含目標進度）

```bash
uv run coach-sessions-summary
```

這會掃描 `data/*.fit` 與 `data/*.tcx`，產生 `sessions_summary.json`。若根目錄有 `training_profile.json`，輸出會包含目標設定、近四週週趨勢、最長單次與 10K 進度，供 AI 報告引用。

### 訓練目標與跑後主觀紀錄

- `training_profile.json`：記錄目前目標、賽事、長期動機與報告偏好，例如金門馬拉松 10K、跑得開心、1K 4:19 的長期火種。
- `training_journal/`：每次跑後可新增一個 JSON，記錄 RPE、開心程度、睡眠、痠痛與備註。檔名建議和活動檔 stem 一致，例如 `training_journal/20260515203341.json`。
- 主觀紀錄不是必填；沒有紀錄時，AI 報告應明確標示未知，不推測心情或疲勞。

### 說明

- 人類可讀模式會印出 `session` 主要欄位與其餘非空欄位列表。
- 若終端機出現 `VIRTUAL_ENV` 與本專案 `.venv` 不符的警告，多半是外層已 `activate` 別的 venv；可先 `deactivate` 再執行 `uv run …`，或依 uv 文件使用 `--active`。

## GitHub Actions

### 整體流程（目標）

之後若要把「教練報告」也自動化，可以照這條線想（**由上到下**）：

1. **`data/` 有新活動檔** — 將 `.fit` commit 並 push 到 GitHub（或用手動跑 workflow）。
2. **解析成 JSON** — 在 CI 裡執行 `uv sync` 與 `uv run coach-parse --json …`，得到結構化的 `session.json`（方便 `jq`、腳本或 API 使用）。
3. **（選用）AI 分析** — 以 Cursor Agent、其他 CLI、或 HTTP API 讀取 `session.json`，產出教練文字（段落、建議、週期化提醒等）。
4. **（選用）寫回 `README.md`** — 只更新 **`## AI 教練分析報告`** 底下的內容；頂部連到本教學的段落不要動。寫入後需 **`git commit` / 開 PR**（並設定 workflow 的 `permissions` 與 token），否則 runner 結束後變更不會進 repo。

**備註**：`.fit` 仍是唯一真相來源；JSON 是解析結果，教練文字是再上一層的衍生產物。不必長期把 `session.json` commit 進 git，用 **artifact** 保存每次 CI 輸出即可；若要版本化報告，可改存 `reports/日期.md` 再 PR。

### 目前已實作（`fit-parse.yml`）

- **工作流程檔**：`.github/workflows/fit-parse.yml`。
- **觸發**：`push` 到 `main` 或 `master` 且變更路徑符合 **`data/**/*.fit`**（避免只改 `data/README.md` 等誤觸發）；或 **Actions → Run workflow**（`workflow_dispatch`）。
- **選檔**：CI 裡**不能**依賴本機那套「mtime 最新」（clone 下來時間戳相近）。因此 **push** 時會用 `git diff-tree` 看**該次 commit** 裡出現的 `data/*.fit`（多個時取列表**最後一個**，行為固定）。**手動執行**可填輸入 `fit_path`；不填則取 `data/*.fit` 依檔名排序的最後一個。
- **產出**：
  - 將 `coach-parse --json` 的 stdout 寫入 `session.json`，以 **artifact** `session-json` 上傳。
  - 安裝 **Cursor CLI** 後以 **Cursor Agent**（`agent -p … --force`，模型見 workflow）讀取 `session.json`，更新根目錄 **`README.md`** 的 `## AI 教練分析報告` 區塊，並寫入 **`analysis/<檔名 stem>.md`**。
  - 將上述變更 **`git commit` / `git push`** 回同一分支（job 已設 `permissions: contents: write`，並依賴預設 `GITHUB_TOKEN`）。
- **Secrets**：在 repo **Settings → Secrets → Actions** 設定 **`CURSOR_API_KEY`**（Cursor 帳號／Cloud Agents API key）。未設定時該 job 會失敗並提示缺少 secret。
- **Repo 設定**：GitHub **Settings → Actions → General → Workflow permissions** 須允許 **Read and write**，否則無法 push。

若你的預設分支不是 `main` / `master`，請編輯 workflow 的 `branches` 列表。若 **`main` 啟用 branch protection** 且禁止 GitHub Actions 直接 push，需調整保護規則或改成開 PR 流程。

### Prompt 範本

- CI 使用的指令模板：`.github/prompts/fit-coach-ci.md`（由 workflow 代入本次 FIT 路徑與檔名 stem）。

### 驗證

- 於 GitHub **Actions** 挑選 **Parse FIT (JSON)** → **Run workflow**（可不選 `fit_path`）並確認該次 run 完成、`session-json` artifact 可下載、`CURSOR_API_KEY` 已設定。

## Cursor：AI 馬拉松教練 skill

專案內含 `.cursor/skills/ai-marathon-coach/SKILL.md`：在對話中附加該 skill 後，可依最新 `data/*.fit` 解讀訓練並更新根目錄 `README.md` 的「AI 教練分析報告」區塊（若你有請模型那樣做）。
