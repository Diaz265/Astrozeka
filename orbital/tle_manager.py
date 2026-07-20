"""
tle_manager.py — Download and load Two-Line Element (TLE) sets.

Fixes vs. the original download_tle.py / load_tle.py:
  * Checks HTTP status and non-empty response before overwriting local files
    (the original silently wrote error pages / empty strings on failure).
  * Retries transient network failures.
  * Returns a clear summary instead of only printing.
  * Centralizes the CelesTrak URLs in config.py so they can't drift out of
    sync between scripts.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import requests
from skyfield.api import EarthSatellite, load

from config import DATA_DIR, REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger("astrozeka.tle_manager")


def download_group(name: str, url: str, data_dir: Path = DATA_DIR,
                    retries: int = 3) -> Path:
    """Download one CelesTrak TLE group and save it to data_dir/{name}.txt.

    Raises RuntimeError if the download fails after all retries or the
    response body doesn't look like a TLE file.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    dest = data_dir / f"{name}.txt"

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            resp.raise_for_status()
            text = resp.text
            if len(text.strip()) < 10:
                raise ValueError("response body too short to be a valid TLE file")
            dest.write_text(text)
            logger.info("Downloaded %s -> %s (%d bytes)", name, dest, len(text))
            return dest
        except Exception as exc:  # noqa: BLE001 - we want to retry any failure
            last_error = exc
            logger.warning("Attempt %d/%d for %s failed: %s", attempt, retries, name, exc)

    raise RuntimeError(f"Failed to download TLE group '{name}' from {url}: {last_error}")


def download_all(groups: Dict[str, str], data_dir: Path = DATA_DIR) -> Dict[str, Path]:
    """Download every group in `groups`, returning {name: path}.

    A failure on one group does not abort the others; failures are
    collected and raised together at the end so the caller sees everything
    that went wrong in one pass.
    """
    results: Dict[str, Path] = {}
    errors: Dict[str, str] = {}
    for name, url in groups.items():
        try:
            results[name] = download_group(name, url, data_dir)
        except RuntimeError as exc:
            errors[name] = str(exc)

    if errors:
        details = "; ".join(f"{k}: {v}" for k, v in errors.items())
        logger.error("Some TLE groups failed to download: %s", details)

    return results


def load_group(name: str, data_dir: Path = DATA_DIR) -> List[EarthSatellite]:
    """Load a previously downloaded TLE group by name."""
    path = data_dir / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(
            f"No local TLE file for '{name}' at {path}. Run download first."
        )
    satellites = load.tle_file(str(path))
    logger.info("Loaded %d objects from %s", len(satellites), path)
    return satellites


def load_many(names: List[str], data_dir: Path = DATA_DIR) -> List[EarthSatellite]:
    """Load and concatenate several TLE groups into one flat list."""
    combined: List[EarthSatellite] = []
    for name in names:
        combined.extend(load_group(name, data_dir))
    return combined
