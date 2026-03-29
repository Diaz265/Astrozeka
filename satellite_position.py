from skyfield.api import load

# Load time scale
ts = load.timescale()
t = ts.now()

# Load satellites from TLE file
satellites = load.tle_file('stations.txt')

# Take the first satellite (ISS)
sat = satellites[0]

# Compute position
geocentric = sat.at(t)
subpoint = geocentric.subpoint()

print("Satellite:", sat.name)
print("Latitude:", subpoint.latitude.degrees)
print("Longitude:", subpoint.longitude.degrees)
print("Altitude (km):", subpoint.elevation.km)