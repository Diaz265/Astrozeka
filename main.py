#!/usr/bin/env python3
"""
main.py — AstroZeka orbital conjunction-screening CLI.

Examples
--------
# Screen currently-cached data (no download), default settings:
    python main.py

# Fresh download, tighter alert distance, look 3 days ahead, also plot the
# single closest conjunction:
    python main.py --download --alert-distance 10 --days 3 --visualize-top

# Only screen the ISS/stations group against Fengyun-1C debris (fast):
    python main.py --primary-groups stations --debris-groups fengyun_debris
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from config import DATA_DIR, DEBRIS_GROUPS, OUTPUT_DIR, PRIMARY_GROUPS
from orbital.collision_detector import CollisionDetector
from orbital.report import print_table, write_csv, write_html_summary
from orbital.tle_manager import download_all, load_many
from orbital.visualizer import plot_pair


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AstroZeka conjunction screening")
    parser.add_argument("--download", action="store_true",
                         help="Re-download all TLE groups from CelesTrak before screening")
    parser.add_argument("--primary-groups", nargs="+", default=["stations"],
                         choices=list(PRIMARY_GROUPS.keys()),
                         help="Which object groups to protect (default: stations)")
    parser.add_argument("--debris-groups", nargs="+", default=["fengyun_debris"],
                         choices=list(DEBRIS_GROUPS.keys()),
                         help="Which debris groups to screen against (default: fengyun_debris)")
    parser.add_argument("--alert-distance", type=float, default=25.0,
                         help="Alert threshold in km (default: 25.0)")
    parser.add_argument("--days", type=float, default=7.0,
                         help="How many days ahead to screen (default: 7)")
    parser.add_argument("--steps-per-day", type=int, default=200,
                         help="Time samples per day (default: 200, ~7 min resolution)")
    parser.add_argument("--top", type=int, default=20,
                         help="How many closest conjunctions to print (default: 20)")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "conjunctions.csv",
                         help="CSV output path")
    parser.add_argument("--visualize-top", action="store_true",
                         help="Render an interactive 3D plot of the single closest conjunction")
    parser.add_argument("--full", action="store_true",
                         help="Screen every primary group against every debris group "
                              "(overrides --primary-groups/--debris-groups)")
    parser.add_argument("--summary", type=Path, default=OUTPUT_DIR / "summary.html",
                         help="HTML summary report path (ranked risk chart + table)")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger("astrozeka.main")

    primary_groups = list(PRIMARY_GROUPS.keys()) if args.full else args.primary_groups
    debris_groups = list(DEBRIS_GROUPS.keys()) if args.full else args.debris_groups

    groups_needed = {**{g: PRIMARY_GROUPS[g] for g in primary_groups},
                     **{g: DEBRIS_GROUPS[g] for g in debris_groups}}

    if args.download:
        print(f"Downloading {len(groups_needed)} TLE group(s) from CelesTrak...")
        download_all(groups_needed, DATA_DIR)
    else:
        missing = [g for g in groups_needed if not (DATA_DIR / f"{g}.txt").exists()]
        if missing:
            print(f"Missing local TLE file(s) for {missing}; downloading those now...")
            download_all({g: groups_needed[g] for g in missing}, DATA_DIR)

    primaries = load_many(primary_groups, DATA_DIR)
    secondaries = load_many(debris_groups, DATA_DIR)
    print(f"Loaded {len(primaries)} primary object(s), {len(secondaries)} debris object(s).")

    detector = CollisionDetector(primaries, secondaries)
    events = detector.screen(
        days=args.days,
        steps_per_day=args.steps_per_day,
        alert_distance_km=args.alert_distance,
        max_pairs_logged=500,
    )

    print_table(events, top_n=args.top)
    csv_path = write_csv(events, args.output)
    summary_path = write_html_summary(events, args.summary, alert_distance_km=args.alert_distance)
    print(f"\nFull results written to {csv_path}")
    print(f"Summary report (open in browser): {summary_path}")

    if args.visualize_top and events:
        closest = events[0]
        primary_obj = next(p for p in primaries if p.name == closest.primary_name)
        secondary_obj = next(s for s in secondaries if s.name == closest.secondary_name)
        html_path = plot_pair(primary_obj, secondary_obj,
                               output_path=OUTPUT_DIR / "closest_conjunction.html")
        print(f"3D visualization of closest conjunction saved to {html_path}")
    elif args.visualize_top:
        print("No conjunctions found, nothing to visualize.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
