from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


AI_HEADING = "## AI 教練分析報告"
COACH_HEADING = "### 看完歷史詳細數據後的教練小提醒："


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _replace_ai_section(readme_text: str, body: str) -> str:
    marker = f"{AI_HEADING}\n"
    start = readme_text.find(marker)
    if start == -1:
        raise ValueError(f"Missing heading: {AI_HEADING}")

    body_start = start + len(marker)
    tail = readme_text[body_start:]
    next_h2 = re.search(r"(?m)^##\s+", tail)
    if next_h2:
        section_end = body_start + next_h2.start()
        suffix = readme_text[section_end:]
    else:
        section_end = len(readme_text)
        suffix = ""

    prefix = readme_text[:body_start]
    rendered = f"{prefix}\n{body.rstrip()}\n"
    if suffix:
        rendered += "\n" + suffix.lstrip("\n")
    return rendered


def _goal_section(profile: dict) -> str:
    goals = profile.get("goals")
    if not isinstance(goals, dict):
        return "\n".join(
            [
                "### 目前目標",
                "",
                "- 尚未設定 `training_profile.json`，目前先以完成訓練與保持規律為主。",
            ],
        )

    lines: list[str] = ["### 目前目標", ""]

    primary = goals.get("primary_race")
    if isinstance(primary, dict):
        event = str(primary.get("event") or "").strip()
        distance = str(primary.get("distance") or "").strip()
        priority = str(primary.get("priority") or "").strip()
        label = " ".join(x for x in (event, distance) if x).strip()
        if label and priority:
            lines.append(f"- 主要目標（{label}）：{priority}。")
        elif label:
            lines.append(f"- 主要目標：{label}。")

    short_term = str(goals.get("short_term") or "").strip()
    if short_term:
        lines.append(f"- 短期方向：{short_term}。")

    emotional = str(goals.get("emotional") or "").strip()
    if emotional:
        lines.append(f"- 情緒目標：{emotional}。")

    long_term = goals.get("long_term_speed")
    if isinstance(long_term, dict):
        memory = str(long_term.get("memory") or "").strip()
        stance = str(long_term.get("stance") or "").strip()
        if memory and stance:
            lines.append(f"- 長期火種（{memory}）：{stance}。")
        elif memory:
            lines.append(f"- 長期火種：{memory}。")

    if len(lines) == 2:
        lines.append("- 目前未提供完整目標描述。")
    return "\n".join(lines)


def _weekly_section(snapshot: dict) -> str:
    lines: list[str] = [
        "### 週趨勢與 10K 進度",
        "",
        "| 週次 | 次數 | 距離 | 時間 | 最長單次 |",
        "| --- | --- | --- | --- | --- |",
    ]
    trends = snapshot.get("recent_weekly_trends")
    if isinstance(trends, list) and trends:
        for item in trends:
            if not isinstance(item, dict):
                continue
            week = item.get("week") or "—"
            run_count = item.get("run_count")
            distance = item.get("table_distance_km") or "—"
            duration = item.get("table_duration_min") or "—"
            longest = item.get("longest_run_km")
            longest_cell = f"{float(longest):.2f} km" if longest is not None else "—"
            count_cell = str(run_count) if run_count is not None else "—"
            lines.append(
                f"| {week} | {count_cell} | {distance} | {duration} | {longest_cell} |",
            )
    else:
        lines.append("| — | — | — | — | — |")

    lines.append("")
    goal_progress = snapshot.get("goal_progress")
    if isinstance(goal_progress, dict):
        longest_km = goal_progress.get("longest_run_km")
        longest_dt = goal_progress.get("longest_run_datetime") or "—"
        if longest_km is not None:
            lines.append(f"- 最長單次（{float(longest_km):.2f} km）：{longest_dt}。")

        progress_percent = goal_progress.get("progress_percent_by_longest_run")
        remaining = goal_progress.get("remaining_km_by_longest_run")
        if progress_percent is not None and remaining is not None:
            lines.append(
                f"- 距離 10K 進度（最長單次）：{float(progress_percent):.1f}%，尚差 {float(remaining):.2f} km。",
            )

        latest_vs_target = goal_progress.get("latest_week_runs_vs_target")
        if latest_vs_target:
            lines.append(f"- 最近一週跑步次數（實際 / 目標）：{latest_vs_target}。")

    activity_count = snapshot.get("activity_count")
    total_distance = snapshot.get("total_distance_km")
    if activity_count is not None and total_distance is not None:
        lines.append(f"- 目前活動數（{int(activity_count)} 筆）：總距離 {float(total_distance):.2f} km。")

    if lines[-1] == "":
        lines.append("- 目前沒有可用的趨勢資料。")
    return "\n".join(lines)


def _analysis_list_section(rows: list[dict], analysis_dir: Path) -> str:
    label_by_stem: dict[str, str] = {}
    for row in rows:
        fit_name = str(row.get("fit_basename") or "")
        stem = Path(fit_name).stem
        if stem:
            label_by_stem[stem] = str(row.get("table_datetime_short") or "")

    groups: dict[str, list[str]] = {}
    for path in sorted(analysis_dir.glob("*.md"), key=lambda p: p.stem):
        stem = path.stem
        key = stem[:6] if len(stem) >= 6 else stem
        groups.setdefault(key, []).append(stem)

    lines = ["### 歷史分析報告列表", ""]
    if not groups:
        lines.append("- 目前尚無分析報告。")
        return "\n".join(lines)

    for month in sorted(groups):
        lines.append(f"- {month}")
        for stem in groups[month]:
            label = label_by_stem.get(stem) or stem
            lines.append(f"  - [{label}](analysis/{stem}.md)")
    return "\n".join(lines)


def _table_cell(value: object) -> str:
    text = str(value).strip() if value is not None else ""
    return text or "—"


def _history_table_section(rows: list[dict], analysis_dir: Path) -> str:
    lines = [
        "### 歷史詳細數據表",
        "",
        "| 日期 | 時長 | 距離 | 配速 | 心率（均／高） | 卡路里 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for row in rows:
        fit_name = str(row.get("fit_basename") or "")
        stem = Path(fit_name).stem
        date_cell = _table_cell(row.get("table_datetime_short"))
        has_analysis = (analysis_dir / f"{stem}.md").exists() if stem else False
        if has_analysis and date_cell != "—":
            date_cell = f"[{date_cell}](analysis/{stem}.md)"

        lines.append(
            "| "
            + " | ".join(
                [
                    date_cell,
                    _table_cell(row.get("table_elapsed_hms")),
                    _table_cell(row.get("table_distance_km")),
                    _table_cell(row.get("table_pace")),
                    _table_cell(row.get("table_avg_max_hr")),
                    _table_cell(row.get("table_calories")),
                ],
            )
            + " |",
        )
    return "\n".join(lines)


def _short_date_label(date_text: str) -> str:
    match = re.match(r"^\d{4}/(\d{2}/\d{2}\s\d{2}:\d{2})$", date_text)
    return match.group(1) if match else date_text


def _extract_pace_seconds(text: str) -> int | None:
    match = re.search(r"(\d+):(\d{2})\s*/km", text)
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def _extract_avg_and_max_hr(text: str) -> tuple[int | None, int | None]:
    nums = [int(x) for x in re.findall(r"\d+", text)]
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], None
    return None, None


def _fallback_notes(rows: list[dict], journal_count: int) -> list[str]:
    if not rows:
        return [
            "- 場次範圍（0 筆）：目前尚無可分析歷史資料",
            f"- 資料範圍限制：主觀感受僅在 training_journal 有紀錄時納入（目前 {journal_count} 筆）",
            "- 非醫療聲明：本內容為訓練紀錄整理用途",
        ]

    labels = [str(r.get("table_datetime_short") or "—") for r in rows]
    distances: list[tuple[float, str]] = []
    paces: list[tuple[int, str]] = []
    avg_hrs: list[int] = []
    max_hrs: list[int] = []

    for row in rows:
        date = str(row.get("table_datetime_short") or "—")
        dist_text = str(row.get("table_distance_km") or "")
        dist_match = re.search(r"(\d+(?:\.\d+)?)\s*km", dist_text)
        if dist_match:
            distances.append((float(dist_match.group(1)), date))

        pace_text = str(row.get("table_pace") or "")
        pace_sec = _extract_pace_seconds(pace_text)
        if pace_sec is not None:
            paces.append((pace_sec, date))

        avg_hr, max_hr = _extract_avg_and_max_hr(str(row.get("table_avg_max_hr") or ""))
        if avg_hr is not None:
            avg_hrs.append(avg_hr)
        if max_hr is not None:
            max_hrs.append(max_hr)

    lines = [f"- 場次範圍（{len(rows)} 筆）：{_short_date_label(labels[0])} 至 {_short_date_label(labels[-1])}"]
    if distances:
        min_dist = min(distances, key=lambda x: x[0])
        max_dist = max(distances, key=lambda x: x[0])
        lines.append(
            f"- 距離（{min_dist[0]:.2f}–{max_dist[0]:.2f} km）：最短 {_short_date_label(min_dist[1])}，最長 {_short_date_label(max_dist[1])}",
        )
    if paces:
        fastest = min(paces, key=lambda x: x[0])
        slowest = max(paces, key=lambda x: x[0])

        def _pace_txt(total_sec: int) -> str:
            m, s = divmod(total_sec, 60)
            return f"{m}:{s:02d} /km"

        lines.append(
            f"- 配速（{_pace_txt(fastest[0])}–{_pace_txt(slowest[0])}）：最快 {_short_date_label(fastest[1])}，最慢 {_short_date_label(slowest[1])}",
        )
    if avg_hrs:
        max_hr_text = f"，峰值最高 {max(max_hrs)} bpm" if max_hrs else ""
        lines.append(f"- 心率（均心率 {min(avg_hrs)}–{max(avg_hrs)} bpm{max_hr_text}）")

    lines.append(
        f"- 資料範圍限制：歷史表為 session 摘要，主觀感受僅在 training_journal 有紀錄時納入（目前 {journal_count} 筆）",
    )
    lines.append("- 非醫療聲明：訓練紀錄整理用途，異常不適請諮詢合格專業")
    return lines[:6]


def _coach_notes_section(rows: list[dict], journal_count: int, coach_notes_path: Path) -> str:
    notes: list[str] = []
    if coach_notes_path.exists():
        text = coach_notes_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            m = re.match(r"^\s*-\s+(.+?)\s*$", line)
            if m:
                notes.append(m.group(1))

    if len(notes) < 4:
        notes = [line[2:] for line in _fallback_notes(rows, journal_count)]

    lines = [COACH_HEADING, ""]
    for note in notes[:6]:
        lines.append(f"- {note}")
    return "\n".join(lines)


def _source_section(rows: list[dict], fit_path: str, fit_stem: str) -> str:
    start_time = "未知"
    for row in rows:
        stem = Path(str(row.get("fit_basename") or "")).stem
        if stem == fit_stem:
            start_time = str(row.get("table_datetime_short") or "未知")
            break
    return "\n".join(
        [
            "### 解析來源",
            "",
            f"本輪已解析 `{fit_path}`，活動起始（UTC+8）為 {start_time}；單次完整分析見 [`analysis/{fit_stem}.md`](analysis/{fit_stem}.md)。",
        ],
    )


def _limits_section() -> str:
    return "\n".join(
        [
            "### 資料限制與免責",
            "",
            "- 歷史表為 FIT/TCX 解析後的 session 層級摘要，用於跨場次基本對照。",
            "- 目標脈絡來自 `training_profile.json`，跑後主觀感受僅在 `training_journal/*.json` 存在時納入。",
            "- 本內容非醫療建議與非診斷，身體若有異常不適請尋求合格專業協助。",
            "- 單次活動的深度解讀與圖表請見各 `analysis/<stem>.md`。",
            "",
            "單次活動完整分析（表／圖／教練文字）見各 `analysis/<stem>.md`。",
        ],
    )


def render_ai_section(
    *,
    summary: dict,
    analysis_dir: Path,
    fit_path: str,
    fit_stem: str,
    coach_notes_path: Path,
) -> str:
    rows = summary.get("rows")
    rows = rows if isinstance(rows, list) else []
    profile = summary.get("training_profile")
    profile = profile if isinstance(profile, dict) else {}
    snapshot = summary.get("training_snapshot")
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    journal_count = int(summary.get("training_journal_entry_count") or 0)

    parts = [
        _goal_section(profile),
        _weekly_section(snapshot),
        _analysis_list_section(rows, analysis_dir),
        _history_table_section(rows, analysis_dir),
        _coach_notes_section(rows, journal_count, coach_notes_path),
        _source_section(rows, fit_path, fit_stem),
        _limits_section(),
    ]
    return "\n\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render README AI coach section deterministically from sessions_summary.json.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("sessions_summary.json"),
        help="Path to sessions summary JSON (default: sessions_summary.json).",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="Path to README file to update (default: README.md).",
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=Path("analysis"),
        help="Directory containing analysis/*.md files.",
    )
    parser.add_argument(
        "--fit-path",
        required=True,
        help="FIT/TCX path parsed in this CI run (for source attribution).",
    )
    parser.add_argument(
        "--fit-stem",
        required=True,
        help="Current activity stem (for source attribution link).",
    )
    parser.add_argument(
        "--coach-notes-path",
        type=Path,
        default=Path("coach_notes.md"),
        help="Markdown file containing LLM-written reminder bullets.",
    )
    args = parser.parse_args()

    summary = _read_json(args.summary)
    readme_text = args.readme.read_text(encoding="utf-8")
    ai_body = render_ai_section(
        summary=summary,
        analysis_dir=args.analysis_dir,
        fit_path=args.fit_path,
        fit_stem=args.fit_stem,
        coach_notes_path=args.coach_notes_path,
    )
    next_text = _replace_ai_section(readme_text, ai_body)
    args.readme.write_text(next_text, encoding="utf-8")
    print(f"Updated {args.readme} from {args.summary}")


if __name__ == "__main__":
    main()
