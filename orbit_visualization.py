import numpy as np
import plotly.graph_objects as go
from skyfield.api import load

# Load satellites
ts = load.timescale()
stations = load.tle_file("stations.txt")
debris = load.tle_file("fengyun_debris.txt")

sat = stations[0]
deb = debris[0]

# Time range (next 6 hours)
hours = np.linspace(0, 6, 200)
times = ts.utc(2026, 3, 28, hours)

# Positions in km
sat_pos = sat.at(times).position.km
deb_pos = deb.at(times).position.km

# -------------------------
# Create Earth sphere
# -------------------------
earth_radius = 6371
u = np.linspace(0, 2*np.pi, 50)
v = np.linspace(0, np.pi, 50)

x = earth_radius * np.outer(np.cos(u), np.sin(v))
y = earth_radius * np.outer(np.sin(u), np.sin(v))
z = earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))

earth = go.Surface(x=x, y=y, z=z, opacity=0.6)

# Satellite orbit
sat_orbit = go.Scatter3d(
    x=sat_pos[0], y=sat_pos[1], z=sat_pos[2],
    mode='lines',
    name='Satellite Orbit'
)

# Debris orbit
deb_orbit = go.Scatter3d(
    x=deb_pos[0], y=deb_pos[1], z=deb_pos[2],
    mode='lines',
    name='Debris Orbit'
)

fig = go.Figure(data=[earth, sat_orbit, deb_orbit])
fig.update_layout(title="AstroZeka Space Debris Visualization")
fig.show()