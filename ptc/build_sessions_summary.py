from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ptc.cli import parse_fit, _pace_min_km

DISPLAY_TZ = ZoneInfo("Asia/Taipei")


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


def _row_for_summary(path: Path, repo_root: Path) -> dict | None:
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
            else ""
        ),
        "table_datetime_short": _datetime_short(win),
    }


def build_summary(repo_root: Path) -> dict:
    data_dir = repo_root / "data"
    fits = sorted(data_dir.glob("*.fit"), key=lambda p: p.name)
    rows: list[dict] = []
    for p in fits:
        r = _row_for_summary(p, repo_root)
        if r:
            rows.append(r)
    return {
        "display_timezone": "Asia/Taipei",
        "display_timezone_note": "Activity windows in rows use Asia/Taipei (UTC+8).",
        "row_order": "data/*.fit sorted by basename (lexicographic ascending); README table row order must match `rows` exactly.",
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
