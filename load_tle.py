# load_tle.py
from skyfield.api import load

# Load time scale
ts = load.timescale()

# Load satellites and debris
stations = load.tle_file('stations.txt')      # e.g., ISS
debris = load.tle_file('fengyun_debris.txt')  # debris fragment

print("Stations loaded:", len(stations))
print("Debris loaded:", len(debris))

# Example: take first object from each
sat = stations[0]
deb = debris[0]

print("Station:", sat.name)
print("Debris:", deb.name)