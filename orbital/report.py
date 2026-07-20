"""
report.py — Turn a list of ConjunctionEvent objects into human- and
machine-readable output. Nothing in the original scripts saved results
anywhere; everything only went to stdout and was lost when the process
exited.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import plotly.graph_objects as go

from orbital.collision_detector import ConjunctionEvent


def print_table(events: List[ConjunctionEvent], top_n: int = 20) -> None:
    if not events:
        print("No conjunctions found under the configured alert distance.")
        return

    print(f"\n{'PRIMARY':<24} {'SECONDARY':<24} {'MIN DIST (km)':>14} {'TIME OF CLOSEST APPROACH'}")
    print("-" * 90)
    for event in events[:top_n]:
        tca = event.time_of_closest_approach.strftime("%Y-%m-%d %H:%M UTC")
        print(f"{event.primary_name[:23]:<24} {event.secondary_name[:23]:<24} "
              f"{event.min_distance_km:>14.3f} {tca}")

    if len(events) > top_n:
        print(f"... and {len(events) - top_n} more (see CSV for full list).")


def write_csv(events: List[ConjunctionEvent], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["primary", "secondary", "min_distance_km", "time_of_closest_approach_utc"])
        for event in events:
            writer.writerow([
                event.primary_name,
                event.secondary_name,
                event.min_distance_km,
                event.time_of_closest_approach.isoformat(),
            ])
    return path


def write_html_summary(
    events: List[ConjunctionEvent],
    path: Path,
    alert_distance_km: float,
    top_n: int = 25,
) -> Path:
    """Render a self-contained, dark-themed HTML report: a horizontal bar
    chart of the closest conjunctions (color-scaled by risk) plus a full
    table below it. This is the file to actually hand to someone —
    the CSV is for further analysis, this is for reading.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not events:
        fig = go.Figure()
        fig.update_layout(
            title=f"AstroZeka Conjunction Summary — no events under {alert_distance_km:.1f} km "
                  f"(generated {generated_at})",
            paper_bgcolor="#0a0a12", plot_bgcolor="#0a0a12", font=dict(color="#e8e8e8"),
            annotations=[dict(text="No conjunctions found in this window.",
                               showarrow=False, font=dict(size=18))],
        )
        fig.write_html(str(path))
        return path

    top_events = events[:top_n]
    labels = [f"{e.primary_name} vs {e.secondary_name}" for e in reversed(top_events)]
    distances = [e.min_distance_km for e in reversed(top_events)]
    hover = [e.time_of_closest_approach.strftime("%Y-%m-%d %H:%M UTC") for e in reversed(top_events)]

    bar = go.Bar(
        x=distances,
        y=labels,
        orientation="h",
        marker=dict(
            color=distances,
            colorscale=[[0, "#ff5252"], [0.5, "#ffb74d"], [1, "#4fc3f7"]],
            cmin=0, cmax=alert_distance_km,
            colorbar=dict(title="km", tickfont=dict(color="#e8e8e8")),
        ),
        text=[f"{d:.1f} km" for d in distances],
        textposition="outside",
        customdata=hover,
        hovertemplate="%{y}<br>Min distance: %{x:.2f} km<br>TCA: %{customdata}<extra></extra>",
    )

    fig = go.Figure(data=[bar])
    fig.add_vline(x=alert_distance_km, line_dash="dash", line_color="#888",
                   annotation_text=f"alert threshold ({alert_distance_km:.0f} km)",
                   annotation_font_color="#e8e8e8")
    fig.update_layout(
        title=(f"AstroZeka Conjunction Summary — {len(events)} event(s) found, "
               f"top {len(top_events)} shown<br>"
               f"<sup>generated {generated_at} · threshold {alert_distance_km:.1f} km</sup>"),
        xaxis_title="Minimum predicted distance (km)",
        paper_bgcolor="#0a0a12", plot_bgcolor="#0a0a12",
        font=dict(color="#e8e8e8"),
        margin=dict(l=220, r=40, t=90, b=40),
        height=max(400, 32 * len(top_events) + 150),
    )
    fig.update_xaxes(gridcolor="#333")
    fig.update_yaxes(gridcolor="#333")

    fig.write_html(str(path))
    return path
