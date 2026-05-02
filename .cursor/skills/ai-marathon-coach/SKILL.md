---
name: ai-marathon-coach
description: Acts as an AI marathon running coach by analyzing the newest FIT file under data/, then updating README.md with session metrics and coaching-oriented notes. Use for personal-train-coach, data/*.fit, marathon or road running analysis, or when refreshing README from the latest activity file.
disable-model-invocation: true
---

# AI 馬拉松教練（FIT → README）

## 何時使用

當使用者在 **personal-train-coach** 專案中需要：以 AI 馬拉松教練角度解讀訓練、**分析最新的 `data/*.fit` 檔案**，並**讀取 `README.md` 檔案，透過最新的 fit 檔案更新資料上去**。

## 工作流程

### 1. 判定最新的 `data/*.fit` 檔案

- 掃描 `data/` 底下副檔名為 `.fit` 的檔案（路徑模式：`data/*.fit`）。
- **最新**以檔案修改時間（mtime）為準；若無法取得可靠 mtime，再以檔名排序作為備援。
- 在後續步驟中明確記錄使用的檔名（含中文檔名時保持原樣）。

### 2. 分析 FIT（二進位）

- `.fit` 為 Garmin FIT 二進位格式，**不要**當成純文字逐行閱讀來萃取數據。
- 若專案內已有解析流程，優先使用 **`uv run coach-parse --json`**（實作於 `ptc/cli.py`）取得結構化摘要。
- 若尚無腳本：用 Python（`fitdecode` 或 `fitparse`）讀取 `record`、`session`、`lap` 等訊息，萃取至少：**日期／開始時間、距離、總時間、平均配速（或可推算）、平均心率（若有）、卡路里（若有）、海拔／爬升（若有）**。
- 若檔案損毀或無跑步相關 session，向使用者說明並停止更新 README，避免寫入錯誤數字。

### 3. AI 馬拉松教練輸出

- 依已萃取的數據，用**馬拉松備賽與週期化訓練**觀點簡短評論（有氧基礎、強度分配、恢復、週跑量趨勢—若僅單次數據則只評論本次與一般原則）。
- 語氣：專業、可執行、避免醫療診斷式宣告；不確定的推論需標示為假設。

### 4. 讀取並更新 `README.md`

- **讀取**專案根目錄的 `README.md`。
- 專案使用教學已移至 **`repo-tutorial.md`**；README 頂部通常僅標題、`repo-tutorial.md` 連結與分隔線——**勿刪改**該教學連結區。
- **透過最新的 fit 檔案更新資料上去**：將「本次檔案關鍵數據＋教練式摘要」寫入 **`## AI 教練分析報告`** 標題之下的內容（可整段替換該節次標題以下、下一個 `##` 之前），勿把使用教學貼回 README。
- 在該區塊註明分析的檔名與（若可取得）活動日期，便於追溯。

## 檢查清單

- [ ] 已確認「最新」的 `data/*.fit` 檔案
- [ ] 數據來自二進位解析，非誤讀文字檔
- [ ] 已讀取現有 `README.md` 再動筆
- [ ] README 更新與該次 FIT 一致，且結構可重複執行不亂版

## 選用延伸

若 FIT 欄位或專案慣例變複雜，可在同目錄新增 `reference.md` 補充欄位對照與範例，並在 `SKILL.md` 頂部以單層連結引用。
