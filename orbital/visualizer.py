"""
visualizer.py — 3D visualization of orbital conjunctions around Earth.

v2 improvements:
  * Earth rendered with a shaded color scale instead of a flat blue blob.
  * The actual point of closest approach is marked and annotated with the
    live distance and UTC time — previously you had two orbit lines and
    had to guess where they nearly met.
  * A dashed "miss vector" line is drawn between the two objects at TCA.
  * Dark theme + camera angle tuned so it doesn't default to looking
    straight down the pole.

Fixes carried over from v1:
  * Hardcoded date replaced with `ts.now()` by default.
  * Always writes an HTML file (fig.show() only works in local/notebook
    contexts and is opt-in).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import plotly.graph_objects as go
from skyfield.api import EarthSatellite, load

EARTH_RADIUS_KM = 6371.0


def _earth_surface(opacity: float = 0.85) -> go.Surface:
    """A simple but decent-looking Earth: a latitude-keyed colorscale so
    poles read lighter (icecap-ish) and mid-latitudes read as a plausible
    land/ocean blue-green, without needing an actual texture file."""
    u = np.linspace(0, 2 * np.pi, 80)
    v = np.linspace(0, np.pi, 80)
    x = EARTH_RADIUS_KM * np.outer(np.cos(u), np.sin(v))
    y = EARTH_RADIUS_KM * np.outer(np.sin(u), np.sin(v))
    z = EARTH_RADIUS_KM * np.outer(np.ones_like(u), np.cos(v))

    lat_color = np.tile(np.cos(v), (len(u), 1))

    return go.Surface(
        x=x, y=y, z=z,
        surfacecolor=lat_color,
        opacity=opacity,
        showscale=False,
        colorscale=[[0, "#0b3d59"], [0.5, "#1c6b8c"], [0.85, "#3f9b6f"], [1, "#e8f4f0"]],
        lighting=dict(ambient=0.6, diffuse=0.8, specular=0.1),
        hoverinfo="skip",
        name="Earth",
    )


def plot_pair(
    primary: EarthSatellite,
    secondary: EarthSatellite,
    hours: float = 6.0,
    steps: int = 300,
    start_time: Optional[datetime] = None,
    output_path: Optional[Path] = None,
    show: bool = False,
) -> Path:
    """Render the orbits of one primary and one secondary object over the
    next `hours`, mark their point of closest approach in that window, and
    save an interactive HTML file. Returns the output path.
    """
    ts = load.timescale()
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    hour_offsets = np.linspace(0, hours, steps)
    dt_list = [start_time + timedelta(hours=float(h)) for h in hour_offsets]
    times = ts.from_datetimes(dt_list)

    primary_pos = primary.at(times).position.km
    secondary_pos = secondary.at(times).position.km

    distances = np.linalg.norm(primary_pos - secondary_pos, axis=0)
    closest_idx = int(np.argmin(distances))
    closest_dist = float(distances[closest_idx])
    closest_time = times[closest_idx].utc_datetime()

    primary_trace = go.Scatter3d(
        x=primary_pos[0], y=primary_pos[1], z=primary_pos[2],
        mode="lines", name=f"Primary: {primary.name}",
        line=dict(width=5, color="#4fc3f7"),
    )
    secondary_trace = go.Scatter3d(
        x=secondary_pos[0], y=secondary_pos[1], z=secondary_pos[2],
        mode="lines", name=f"Secondary (debris): {secondary.name}",
        line=dict(width=5, color="#ff7043"),
    )

    approach_markers = go.Scatter3d(
        x=[primary_pos[0, closest_idx], secondary_pos[0, closest_idx]],
        y=[primary_pos[1, closest_idx], secondary_pos[1, closest_idx]],
        z=[primary_pos[2, closest_idx], secondary_pos[2, closest_idx]],
        mode="markers+text",
        marker=dict(size=6, color=["#4fc3f7", "#ff7043"], symbol="diamond"),
        text=[primary.name, secondary.name],
        textposition="top center",
        showlegend=False,
        hoverinfo="skip",
    )

    miss_vector = go.Scatter3d(
        x=[primary_pos[0, closest_idx], secondary_pos[0, closest_idx]],
        y=[primary_pos[1, closest_idx], secondary_pos[1, closest_idx]],
        z=[primary_pos[2, closest_idx], secondary_pos[2, closest_idx]],
        mode="lines",
        line=dict(width=3, color="yellow", dash="dash"),
        name=f"Closest approach: {closest_dist:.1f} km",
    )

    fig = go.Figure(data=[_earth_surface(), primary_trace, secondary_trace,
                          miss_vector, approach_markers])

    tca_str = closest_time.strftime("%Y-%m-%d %H:%M UTC")
    fig.update_layout(
        title=dict(
            text=(f"AstroZeka Conjunction View — {primary.name} vs {secondary.name}<br>"
                  f"<sup>Closest approach: {closest_dist:.2f} km at {tca_str} "
                  f"(window: next {hours:.0f}h from {start_time.strftime('%Y-%m-%d %H:%M UTC')})</sup>"),
        ),
        scene=dict(
            aspectmode="data",
            xaxis=dict(showbackground=False, showticklabels=False, title=""),
            yaxis=dict(showbackground=False, showticklabels=False, title=""),
            zaxis=dict(showbackground=False, showticklabels=False, title=""),
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.9)),
        ),
        paper_bgcolor="#0a0a12",
        font=dict(color="#e8e8e8"),
        legend=dict(bgcolor="rgba(20,20,30,0.7)"),
        margin=dict(l=0, r=0, t=80, b=0),
    )

    if output_path is None:
        output_path = Path("outputs") / "orbit_visualization.html"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))

    if show:
        fig.show()

    return output_path
