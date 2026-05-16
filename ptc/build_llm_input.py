from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from ptc.build_sessions_summary import build_summary
from ptc.cli import _pace_min_km, parse_fit, parse_tcx


def _json_safe(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _latest_data_file(repo_root: Path) -> Path | None:
    data_dir = repo_root / "data"
    files = list(data_dir.glob("*.fit")) + list(data_dir.glob("*.tcx"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def _load_summary(repo_root: Path, summary_path: Path) -> dict:
    payload = _read_json(summary_path)
    if payload is not None:
        return payload
    return build_summary(repo_root)


def _parse_session_from_fit(path: Path) -> dict | None:
    if not path.exists():
        return None
    if path.suffix.lower() == ".tcx":
        return parse_tcx(path)
    return parse_fit(path)


def _compact_current_activity(
    session_payload: dict | None,
    fit_path: str,
    fit_stem: str,
    matching_row: dict | None,
) -> dict:
    current: dict[str, object] = {
        "fit_path": fit_path,
        "fit_stem": fit_stem,
    }

    if matching_row:
        current.update(
            {
                "activity_start_utc8": matching_row.get("table_datetime_short"),
                "elapsed": matching_row.get("table_elapsed_hms"),
                "distance": matching_row.get("table_distance_km"),
                "pace": matching_row.get("table_pace"),
                "avg_max_hr": matching_row.get("table_avg_max_hr"),
                "calories": matching_row.get("table_calories"),
                "device": matching_row.get("device"),
                "sport": matching_row.get("sport"),
            },
        )

    session = session_payload.get("session") if isinstance(session_payload, dict) else None
    file_id = session_payload.get("file_id") if isinstance(session_payload, dict) else None
    if not isinstance(session, dict):
        return current

    distance_m = session.get("total_distance")
    timer_s = session.get("total_timer_time") or session.get("total_elapsed_time")
    pace = _pace_min_km(distance_m, timer_s)
    if pace:
        pace = pace.replace(" min/km", " /km")

    current.update(
        {
            "start_time_raw": session.get("start_time"),
            "distance_m": distance_m,
            "timer_s": timer_s,
            "pace_from_session": pace,
            "avg_hr": session.get("avg_heart_rate"),
            "max_hr": session.get("max_heart_rate"),
            "min_hr": session.get("min_heart_rate"),
            "calories_raw": session.get("total_calories"),
            "device_name": (file_id or {}).get("product_name") if isinstance(file_id, dict) else None,
        },
    )
    return current


def _compact_profile(summary: dict) -> dict:
    profile = summary.get("training_profile")
    if not isinstance(profile, dict):
        return {}
    goals = profile.get("goals") if isinstance(profile.get("goals"), dict) else {}
    prefs = (
        profile.get("training_preferences")
        if isinstance(profile.get("training_preferences"), dict)
        else {}
    )
    return {
        "primary_race": goals.get("primary_race"),
        "short_term": goals.get("short_term"),
        "emotional": goals.get("emotional"),
        "long_term_speed": goals.get("long_term_speed"),
        "weekly_runs_target": prefs.get("weekly_runs_target"),
        "priority_order": prefs.get("priority_order"),
    }


def _compact_recent_history(rows: list[dict], history_limit: int) -> list[dict]:
    selected = rows[-history_limit:] if history_limit > 0 else rows
    output: list[dict] = []
    for row in selected:
        output.append(
            {
                "fit_stem": Path(str(row.get("fit_basename") or "")).stem,
                "datetime": row.get("table_datetime_short"),
                "elapsed": row.get("table_elapsed_hms"),
                "distance": row.get("table_distance_km"),
                "pace": row.get("table_pace"),
                "avg_max_hr": row.get("table_avg_max_hr"),
                "calories": row.get("table_calories"),
                "has_analysis": row.get("has_analysis"),
            },
        )
    return output


def build_llm_input(
    *,
    repo_root: Path,
    summary_path: Path,
    session_path: Path,
    fit_path_arg: str | None,
    history_limit: int,
) -> dict:
    summary = _load_summary(repo_root, summary_path)
    rows = summary.get("rows")
    rows = rows if isinstance(rows, list) else []

    fit_path = fit_path_arg
    if not fit_path:
        session_payload = _read_json(session_path)
        if session_payload and isinstance(session_payload.get("file"), str):
            fit_path = str(session_payload["file"])
    if not fit_path and rows:
        fit_path = str(rows[-1].get("fit_path") or "")
    if not fit_path:
        latest = _latest_data_file(repo_root)
        fit_path = str(latest.relative_to(repo_root)) if latest else ""

    fit_stem = Path(fit_path).stem if fit_path else ""
    matching_row = next(
        (
            row
            for row in rows
            if Path(str(row.get("fit_basename") or "")).stem == fit_stem
        ),
        rows[-1] if rows else None,
    )

    session_payload = _read_json(session_path)
    if session_payload is None and fit_path:
        maybe_path = Path(fit_path)
        if not maybe_path.is_absolute():
            maybe_path = repo_root / maybe_path
        session_payload = _parse_session_from_fit(maybe_path.resolve())

    snapshot = summary.get("training_snapshot")
    snapshot = snapshot if isinstance(snapshot, dict) else {}

    payload = {
        "schema_version": 1,
        "purpose": "Compact context for LLM coaching text generation.",
        "display_timezone": summary.get("display_timezone") or "Asia/Taipei",
        "current_activity": _compact_current_activity(session_payload, fit_path, fit_stem, matching_row),
        "goal_context": _compact_profile(summary),
        "trend_context": {
            "activity_count": snapshot.get("activity_count"),
            "total_distance_km": snapshot.get("total_distance_km"),
            "recent_weekly_trends": snapshot.get("recent_weekly_trends"),
            "goal_progress": snapshot.get("goal_progress"),
            "training_journal_entry_count": summary.get("training_journal_entry_count"),
        },
        "recent_history": _compact_recent_history(rows, history_limit),
        "output_requirements": {
            "coach_notes": {
                "language": "zh-TW",
                "bullet_count": "4-6",
                "single_line_each": True,
                "must_include_scope_limit_and_non_medical_disclaimer": True,
            },
        },
    }
    return _json_safe(payload)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build compact llm_input.json from sessions summary/session sources.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root (default: current directory).",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("sessions_summary.json"),
        help="Path to sessions_summary.json (default: sessions_summary.json).",
    )
    parser.add_argument(
        "--session",
        type=Path,
        default=Path("session.json"),
        help="Path to session.json (default: session.json).",
    )
    parser.add_argument(
        "--fit-path",
        default=None,
        help="Current fit/tcx path (optional; auto-detected when omitted).",
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        default=8,
        help="Number of recent history rows to include (default: 8).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("llm_input.json"),
        help="Output path (default: llm_input.json).",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    summary_path = args.summary if args.summary.is_absolute() else repo_root / args.summary
    session_path = args.session if args.session.is_absolute() else repo_root / args.session
    output_path = args.output if args.output.is_absolute() else repo_root / args.output

    payload = build_llm_input(
        repo_root=repo_root,
        summary_path=summary_path,
        session_path=session_path,
        fit_path_arg=args.fit_path,
        history_limit=max(args.history_limit, 0),
    )

    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
