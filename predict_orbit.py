# predict_orbit.py
import numpy as np
from skyfield.api import load

ts = load.timescale()
stations = load.tle_file('stations.txt')
debris = load.tle_file('fengyun_debris.txt')

sat = stations[0]
deb = debris[0]

# Time points (next 24 hours, 200 points)
hours = np.linspace(0, 24, 200)
times = ts.utc(2026, 3, 28, hours)

# Get 3D positions in km
pos_sat = sat.at(times).position.km
pos_deb = deb.at(times).position.km

# Compute distances
distances = np.linalg.norm(pos_sat - pos_deb, axis=0)

print("Minimum distance (km) in next 24h:", distances.min())