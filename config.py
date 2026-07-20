"""
config.py — Central configuration for AstroZeka.

Keeping every constant in one place means the CLI, the detector, and the
visualizer never disagree about what "close" means or where data lives.
"""

from pathlib import Path

# -----------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "tle"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# -----------------------------------------------------------------------
# CelesTrak TLE sources
# -----------------------------------------------------------------------
# "Primary" objects: things we are protecting (crewed stations, active sats).
PRIMARY_GROUPS = {
    "stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
    "active": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
    "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
    "oneweb": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle",
    "kuiper": "https://celestrak.org/NORAD/elements/gp.php?GROUP=kuiper&FORMAT=tle",
}

# "Secondary" objects: known debris clouds we screen against.
DEBRIS_GROUPS = {
    "fengyun_debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=fengyun-1c-debris&FORMAT=tle",
    "cosmos_debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle",
    "iridium_debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle",
}

ALL_GROUPS = {**PRIMARY_GROUPS, **DEBRIS_GROUPS}

# -----------------------------------------------------------------------
# Screening defaults
# -----------------------------------------------------------------------
# NOTE: real-world conjunction screening (e.g. 18th SDS / CSpOC) typically
# flags anything inside a few tens of km for a closer look, because TLE
# propagation error alone can be kilometers. The original scripts used a
# 200 km threshold with only 500 samples over 7 days, which is so coarse it
# would miss most close approaches AND flag near-everything as "risky".
# We default to a tighter, more meaningful screening distance and denser
# time sampling, both overridable from the CLI.
DEFAULT_ALERT_DISTANCE_KM = 25.0
DEFAULT_PREDICTION_DAYS = 7
DEFAULT_TIME_STEPS_PER_DAY = 200  # samples/day; ~7 min resolution

REQUEST_TIMEOUT_SECONDS = 30
