# personal-train-coach

使用方式見 [repo-tutorial.md](repo-tutorial.md)。

---

## AI 教練分析報告

- **解析檔**：`data/20260418173835.fit`。**活動時間**（`session.json` 之 `start_time` → `timestamp`，UTC）：2026-04-18 09:38:35+00:00 至 2026-04-18 10:18:20+00:00。
- **本筆數據**：跑步；`total_elapsed_time`／`total_timer_time` 2385.43 s；`total_distance` 4766.21 m；`avg_heart_rate` 147（`max` 160／`min` 90）；`avg_speed` 1.998 m/s（同檔亦列 `enhanced_avg_speed`）。`total_calories` 329；`avg_temperature` 29；爬升／下降 `total_ascent` 5、`total_descent` 6。
- **週期化視角（僅單次檔，週量趨勢未知）**：此堂 `total_elapsed_time` 2385.43 s、距離 `total_distance` 4766.21 m 的連續跑，平均心率與速度搭配下，**假設**對個人屬可控有氧節奏，則可作為馬拉松打底期常見的「維持心肺與跑感」課型；因無多週跑量與長課紀錄，無法判斷本週是否過量或是否需加長距離，僅能建議以「隔日主觀恢復＋（若有）靜息心率／HRV」決定下一日強度，避免在資訊不足時硬加量。
- **強度分佈**：檔內無分區時間或乳酸閾值欄位，**無法**還原 Zone 比例；若要優化有氧／閾值／間歇配比，需額外紀錄或更多 `.fit` 一併檢視。
- **恢復與風險**：非醫療建議。無睡眠、傷痛史或實驗室數據於本檔；若跑後異常疲勞或疼痛，應降低下一堂負荷並尋求合格專業協助，而非依單次平均值自行診斷。

更完整敘事見 `analysis/20260418173835.md`（同樣僅引用 `session.json` 可得欄位）。
