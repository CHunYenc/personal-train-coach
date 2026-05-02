from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitdecode


def find_latest_fit(data_dir: Path) -> Path:
    fits = list(data_dir.glob("*.fit"))
    if not fits:
        raise SystemExit(f"No .fit files in {data_dir}")
    return max(fits, key=lambda p: p.stat().st_mtime)


def parse_fit(path: Path) -> dict:
    """Extract file_id and last session (single-activity exports)."""
    file_id: dict = {}
    sessions: list[dict] = []
    with fitdecode.FitReader(str(path)) as fit:
        for frame in fit:
            if frame.frame_type != fitdecode.FIT_FRAME_DATA:
                continue
            if frame.name == "file_id":
                file_id = {
                    f.name: f.value
                    for f in frame.fields
                    if f.value is not None
                }
            elif frame.name == "session":
                sessions.append(
                    {
                        f.name: f.value
                        for f in frame.fields
                        if f.value is not None
                    }
                )
    session = sessions[-1] if sessions else None
    return {"file": str(path), "file_id": file_id, "session": session}


def _pace_min_km(distance_m: float | None, time_s: float | None) -> str | None:
    if not distance_m or distance_m <= 0 or not time_s or time_s <= 0:
        return None
    sec_per_km = time_s / (distance_m / 1000.0)
    m, s = divmod(int(round(sec_per_km)), 60)
    return f"{m}:{s:02d} min/km"


def print_human(summary: dict) -> None:
    path = summary["file"]
    s = summary.get("session")
    print(f"File: {path}")
    if not s:
        print("No session message found in FIT.")
        return

    dist = s.get("total_distance")
    elapsed = s.get("total_elapsed_time")
    timer = s.get("total_timer_time")
    start = s.get("start_time")
    sport = s.get("sport")
    sub = s.get("sub_sport")

    print(f"Start: {start}")
    print(f"Sport: {sport}  Sub-sport: {sub}")
    if dist is not None:
        print(f"Distance: {dist / 1000:.3f} km")
    if elapsed is not None:
        print(f"Elapsed: {elapsed:.0f} s")
    if timer is not None:
        print(f"Timer: {timer:.0f} s")
    pace = _pace_min_km(dist, timer or elapsed)
    if pace:
        print(f"Pace (from time/distance): {pace}")

    for label, key in (
        ("Avg HR", "avg_heart_rate"),
        ("Max HR", "max_heart_rate"),
        ("Calories", "total_calories"),
        ("Ascent", "total_ascent"),
        ("Avg cadence", "avg_running_cadence"),
        ("Avg speed (m/s)", "avg_speed"),
    ):
        if key in s:
            print(f"{label}: {s[key]}")

    print("\n--- raw session fields (non-null) ---")
    for k in sorted(s):
        print(f"  {k}: {s[k]}")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    default_data = root / "data"

    p = argparse.ArgumentParser(
        description="Parse Garmin FIT; default = newest file in data/",
    )
    p.add_argument(
        "fit_path",
        nargs="?",
        default=None,
        help="Path to .fit (default: latest mtime under data/)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Print full summary as JSON",
    )
    args = p.parse_args()

    if args.fit_path:
        fit_path = Path(args.fit_path).expanduser().resolve()
    else:
        fit_path = find_latest_fit(default_data)

    if not fit_path.is_file():
        raise SystemExit(f"Not a file: {fit_path}")

    summary = parse_fit(fit_path)

    if args.json:
        print(json.dumps(summary, default=str, indent=2, ensure_ascii=False))
    else:
        print_human(summary)


if __name__ == "__main__":
    main()
