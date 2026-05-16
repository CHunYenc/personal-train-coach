from __future__ import annotations

import argparse
from collections import defaultdict
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ptc.cli import parse_fit, parse_tcx, _pace_min_km

DISPLAY_TZ = ZoneInfo("Asia/Taipei")


def _read_json(path: Path) -> object | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_training_profile(repo_root: Path) -> dict:
    payload = _read_json(repo_root / "training_profile.json")
    return payload if isinstance(payload, dict) else {}


def _load_training_journal(repo_root: Path) -> dict[str, dict]:
    journal_dir = repo_root / "training_journal"
    entries: dict[str, dict] = {}
    if not journal_dir.is_dir():
        return entries

    for path in sorted(journal_dir.glob("*.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            continue
        key = payload.get("activity_stem")
        if not key:
            key = path.stem
        entries[str(key)] = payload
    return entries


def _coerce_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


def _to_utc8_label(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    local = dt.astimezone(DISPLAY_TZ)
    return local.isoformat(sep=" ", timespec="seconds")


def _device_label(file_id: dict) -> str:
    name = file_id.get("product_name")
    if name:
        return str(name)
    mfr = file_id.get("manufacturer")
    if mfr:
        return str(mfr)
    return ""


def _elapsed_hms(total_seconds: float | None) -> str:
    if total_seconds is None:
        return ""
    s = int(round(total_seconds))
    h, rem = divmod(s, 3600)
    m, s2 = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s2:02d}"
    return f"{m}:{s2:02d}"


def _datetime_short(win: str) -> str:
    """Format activity_window_utc8 start as 'YYYY/MM/DD HH:mm'."""
    if not win:
        return ""
    start_part = win.split(" → ")[0].strip()
    try:
        date_str, rest = start_part.split(" ", 1)
        return f"{date_str.replace('-', '/')} {rest[:5]}"
    except (ValueError, IndexError):
        return ""


def _row_start_datetime(row: dict) -> datetime | None:
    win = row.get("activity_window_utc8")
    if not isinstance(win, str) or not win:
        return None
    start_part = win.split(" → ")[0].strip()
    return _coerce_datetime(start_part)


def _distance_goal_km(profile: dict) -> float | None:
    goals = profile.get("goals")
    if not isinstance(goals, dict):
        return None
    primary_race = goals.get("primary_race")
    if not isinstance(primary_race, dict):
        return None
    distance = primary_race.get("distance")
    if not isinstance(distance, str):
        return None

    match = re.search(r"(\d+(?:\.\d+)?)\s*K", distance, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _training_snapshot(rows: list[dict], profile: dict) -> dict:
    weeks: dict[str, dict] = defaultdict(
        lambda: {
            "run_count": 0,
            "distance_km": 0.0,
            "duration_min": 0.0,
            "longest_run_km": 0.0,
            "week_start_utc8": "",
        },
    )

    longest_row: dict | None = None
    total_distance_km = 0.0
    for row in rows:
        dist_m = row.get("distance_m") or 0
        timer_s = row.get("timer_s") or 0
        distance_km = float(dist_m) / 1000
        total_distance_km += distance_km

        previous_longest_km = (
            float(longest_row.get("distance_m") or 0) / 1000
            if longest_row
            else 0.0
        )
        if longest_row is None or distance_km > previous_longest_km:
            longest_row = row

        start_dt = _row_start_datetime(row)
        if start_dt is None:
            continue
        iso = start_dt.isocalendar()
        week_key = f"{iso.year}-W{iso.week:02d}"
        week = weeks[week_key]
        if not week["week_start_utc8"]:
            week_start = (start_dt - timedelta(days=start_dt.weekday())).date()
            week["week_start_utc8"] = week_start.isoformat()
        week["run_count"] += 1
        week["distance_km"] += distance_km
        week["duration_min"] += float(timer_s) / 60
        week["longest_run_km"] = max(float(week["longest_run_km"]), distance_km)

    weekly_trends = []
    for week_key in sorted(weeks):
        week = weeks[week_key]
        weekly_trends.append(
            {
                "week": week_key,
                "week_start_utc8": week["week_start_utc8"],
                "run_count": int(week["run_count"]),
                "distance_km": round(float(week["distance_km"]), 2),
                "duration_min": round(float(week["duration_min"]), 1),
                "longest_run_km": round(float(week["longest_run_km"]), 2),
                "table_distance_km": f"{float(week['distance_km']):.2f} km",
                "table_duration_min": f"{float(week['duration_min']):.0f} min",
            },
        )

    target_distance_km = _distance_goal_km(profile)
    longest_distance_km = (
        float(longest_row.get("distance_m") or 0) / 1000 if longest_row else 0.0
    )
    progress: dict = {
        "longest_run_km": round(longest_distance_km, 2),
        "longest_run_datetime": (
            longest_row.get("table_datetime_short") if longest_row else ""
        ),
    }
    if target_distance_km:
        progress.update(
            {
                "target_distance_km": target_distance_km,
                "progress_percent_by_longest_run": round(
                    min(longest_distance_km / target_distance_km * 100, 100),
                    1,
                ),
                "remaining_km_by_longest_run": round(
                    max(target_distance_km - longest_distance_km, 0),
                    2,
                ),
            },
        )

    training_preferences = profile.get("training_preferences")
    weekly_runs_target = None
    if isinstance(training_preferences, dict):
        weekly_runs_target = training_preferences.get("weekly_runs_target")
    latest_week = weekly_trends[-1] if weekly_trends else None
    if weekly_runs_target and latest_week:
        progress["latest_week_runs_vs_target"] = (
            f"{latest_week['run_count']} / {weekly_runs_target}"
        )

    return {
        "activity_count": len(rows),
        "total_distance_km": round(total_distance_km, 2),
        "weekly_trends": weekly_trends,
        "recent_weekly_trends": weekly_trends[-4:],
        "goal_progress": progress,
    }


def _row_for_summary(path: Path, repo_root: Path) -> dict | None:
    if path.suffix.lower() == ".tcx":
        summary = parse_tcx(path.resolve())
    else:
        summary = parse_fit(path.resolve())
    session = summary.get("session")
    if not session:
        return None
    file_id = summary.get("file_id") or {}
    start = _coerce_datetime(session.get("start_time"))
    end = _coerce_datetime(session.get("timestamp"))
    win = ""
    if start and end:
        win = f"{_to_utc8_label(start)} → {_to_utc8_label(end)}"
    elif start:
        win = _to_utc8_label(start)

    rel = path.resolve().relative_to(repo_root.resolve())
    timer = session.get("total_timer_time")
    if timer is None:
        timer = session.get("total_elapsed_time")
    dist = session.get("total_distance")
    table_elapsed = f"{float(timer):.2f} s" if timer is not None else ""
    table_distance = f"{float(dist):.2f} m" if dist is not None else ""
    min_hr = session.get("min_heart_rate")
    avg_hr = session.get("avg_heart_rate")
    max_hr = session.get("max_heart_rate")
    hr = ""
    if min_hr is not None and avg_hr is not None and max_hr is not None:
        hr = f"{int(min_hr)}／{int(avg_hr)}／{int(max_hr)} bpm"

    av_sp = session.get("enhanced_avg_speed")
    if av_sp is None:
        av_sp = session.get("avg_speed")
    mx_sp = session.get("enhanced_max_speed")
    if mx_sp is None:
        mx_sp = session.get("max_speed")
    spd = ""
    if av_sp is not None and mx_sp is not None:
        spd = f"{float(av_sp):.3f}／{float(mx_sp):.3f} m/s"

    cal = session.get("total_calories")
    tem = session.get("avg_temperature")
    asc = session.get("total_ascent")
    des = session.get("total_descent")
    return {
        "fit_basename": path.name,
        "fit_path": str(rel).replace("\\", "/"),
        "activity_window_utc8": win,
        "timer_s": timer,
        "distance_m": dist,
        "heart_rate_min_avg_max": hr,
        "speed_avg_max": spd,
        "calories": cal,
        "avg_temperature": tem,
        "ascent": asc,
        "descent": des,
        "device": _device_label(file_id),
        "sport": session.get("sport"),
        "table_elapsed": table_elapsed,
        "table_distance": table_distance,
        "table_calories": str(cal) if cal is not None else "",
        "table_elapsed_hms": _elapsed_hms(timer),
        "table_distance_km": f"{float(dist) / 1000:.2f} km" if dist is not None else "",
        "table_pace": ((_pace_min_km(dist, timer) or "").replace("min/km", "/km")).strip(),
        "table_avg_max_hr": (
            f"{int(avg_hr)}／{int(max_hr)} bpm"
            if avg_hr is not None and max_hr is not None
            else (f"{int(avg_hr)} bpm" if avg_hr is not None else "")
        ),
        "table_datetime_short": _datetime_short(win),
    }


def build_summary(repo_root: Path) -> dict:
    data_dir = repo_root / "data"
    analysis_dir = repo_root / "analysis"
    profile = _load_training_profile(repo_root)
    journal = _load_training_journal(repo_root)
    all_files = list(data_dir.glob("*.fit")) + list(data_dir.glob("*.tcx"))
    rows: list[dict] = []
    for p in all_files:
        r = _row_for_summary(p, repo_root)
        if r:
            r["has_analysis"] = (analysis_dir / f"{p.stem}.md").exists()
            if p.stem in journal:
                r["subjective"] = journal[p.stem]
            rows.append(r)
    rows.sort(key=lambda r: r.get("activity_window_utc8") or "")
    return {
        "display_timezone": "Asia/Taipei",
        "display_timezone_note": "Activity windows in rows use Asia/Taipei (UTC+8).",
        "row_order": "sorted by activity_window_utc8 ascending (chronological); README table row order must match `rows` exactly.",
        "training_profile": profile,
        "training_journal_entry_count": len(journal),
        "training_snapshot": _training_snapshot(rows, profile),
        "rows": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Scan data/*.fit and write sessions_summary.json for README history table.",
    )
    ap.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of package root)",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("sessions_summary.json"),
        help="Output path (default: ./sessions_summary.json)",
    )
    args = ap.parse_args()
    root = args.repo_root
    if root is None:
        root = Path(__file__).resolve().parent.parent
    out = args.output
    if not out.is_absolute():
        out = Path.cwd() / out
    payload = build_summary(root)
    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out} ({len(payload['rows'])} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
