# `data/`

這個資料夾用來放 **Garmin／跑錶／裝置匯出的 `.fit` 活動檔**（FIT 二進位格式）。本專案會用 `coach-parse` 把它們轉成結構化摘要（例如 JSON），供本機或 CI 後續流程使用。

## 使用方式與慣例

- 檔名可依裝置匯出習慣命名；解析時請以實際路徑為準。
- `.fit` 請勿當成純文字檔閱讀；請用專案內的解析指令（見 [repo-tutorial.md](../repo-tutorial.md)）。
- 若檔案含個資或軌跡等敏感內容，請自行評估是否適合提交到 git／公開 repo。

完整 CLI、`uv` 與 GitHub Actions 說明請見 [repo-tutorial.md](../repo-tutorial.md)。
