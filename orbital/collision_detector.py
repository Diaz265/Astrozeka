"""
collision_detector.py — Conjunction (close-approach) screening.

This replaces astrozeka_collision_system.py / collision_alert.py /
predict_orbit.py, which all shared the same bugs:

  1. HARDCODED DATE: `ts.utc(2026, 3, 28, hours)` always screens the same
     fixed 24h/7d window starting March 28 2026, regardless of when the
     script is actually run. A "collision alert" system that always looks
     at the same historical window isn't predicting anything current.
     -> Fixed: defaults to `ts.now()`, override with `start_time`.

  2. INCONSISTENT ALERT_DISTANCE across scripts (200 km vs 50 km) with no
     shared source of truth.
     -> Fixed: single default in config.py, override per call.

  3. No record of *when* the closest approach happens, only *how close*.
     -> Fixed: ConjunctionEvent stores time_of_closest_approach.

  4. No de-duplication / sorting -- alerts were reported in loop order.
     -> Fixed: results always sorted by ascending distance.

  5. Silent quadratic blow-up: screening N primaries x M debris with dense
     time sampling is O(N*M*T). For N=50, M=5000 debris, T=1400 samples
     that's ~350M vector norms. We keep the same numpy-vectorized-over-time
     approach (fast per pair) but expose `steps` so the caller can trade
     resolution for runtime, and log progress so a long run isn't silent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import numpy as np
from skyfield.api import EarthSatellite, load
from skyfield.timelib import Time

from config import DEFAULT_ALERT_DISTANCE_KM, DEFAULT_PREDICTION_DAYS, DEFAULT_TIME_STEPS_PER_DAY

logger = logging.getLogger("astrozeka.collision_detector")


@dataclass
class ConjunctionEvent:
    primary_name: str
    secondary_name: str
    min_distance_km: float
    time_of_closest_approach: datetime

    def __str__(self) -> str:
        tca = self.time_of_closest_approach.strftime("%Y-%m-%d %H:%M UTC")
        return (f"{self.primary_name!r} <-> {self.secondary_name!r}: "
                f"{self.min_distance_km:.2f} km at {tca}")


class CollisionDetector:
    """Screens a set of "primary" objects (things to protect) against a
    set of "secondary" objects (debris) for close approaches over a
    forward time window, using SGP4 propagation via Skyfield.

    This is a coarse *screening* tool, not a conjunction-probability (Pc)
    calculator: it flags pairs whose propagated positions come within a
    distance threshold. TLE propagation error is itself commonly several
    hundred meters to a few km, growing with time-since-epoch, so treat
    "min_distance_km" as an estimate, not a certified miss distance.
    """

    def __init__(self, primaries: List[EarthSatellite], secondaries: List[EarthSatellite]):
        if not primaries:
            raise ValueError("primaries list is empty — nothing to protect")
        if not secondaries:
            raise ValueError("secondaries list is empty — nothing to screen against")
        self.primaries = primaries
        self.secondaries = secondaries
        self.ts = load.timescale()

    def _time_grid(self, start_time: Optional[datetime], days: int, steps_per_day: int) -> Time:
        if start_time is None:
            start_time = datetime.now(timezone.utc)
        elif start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        total_steps = max(2, int(days * steps_per_day))
        offsets_days = np.linspace(0, days, total_steps)
        dt_list = [start_time + timedelta(days=float(d)) for d in offsets_days]
        return self.ts.from_datetimes(dt_list)

    def screen(
        self,
        start_time: Optional[datetime] = None,
        days: int = DEFAULT_PREDICTION_DAYS,
        steps_per_day: int = DEFAULT_TIME_STEPS_PER_DAY,
        alert_distance_km: float = DEFAULT_ALERT_DISTANCE_KM,
        max_pairs_logged: int = 0,
    ) -> List[ConjunctionEvent]:
        """Run the screening and return events sorted by ascending distance.

        max_pairs_logged: if >0, log progress every N pairs (useful for
        large debris catalogs where the run can take a while).
        """
        times = self._time_grid(start_time, days, steps_per_day)
        events: List[ConjunctionEvent] = []

        # Precompute secondary positions once — they're reused for every
        # primary, so this alone cuts the work roughly in half versus the
        # original nested loop, which recomputed debris positions for
        # every single primary.
        secondary_positions = [(deb, deb.at(times).position.km) for deb in self.secondaries]

        total_pairs = len(self.primaries) * len(self.secondaries)
        pair_count = 0

        for sat in self.primaries:
            pos_sat = sat.at(times).position.km
            for deb, pos_deb in secondary_positions:
                pair_count += 1
                if max_pairs_logged and pair_count % max_pairs_logged == 0:
                    logger.info("Screened %d/%d pairs...", pair_count, total_pairs)

                distances = np.linalg.norm(pos_sat - pos_deb, axis=0)
                idx = int(np.argmin(distances))
                min_dist = float(distances[idx])

                if min_dist < alert_distance_km:
                    tca = times[idx].utc_datetime()
                    events.append(ConjunctionEvent(
                        primary_name=sat.name,
                        secondary_name=deb.name,
                        min_distance_km=round(min_dist, 3),
                        time_of_closest_approach=tca,
                    ))

        events.sort(key=lambda e: e.min_distance_km)
        logger.info("Screening complete: %d conjunction(s) under %.1f km threshold",
                    len(events), alert_distance_km)
        return events
