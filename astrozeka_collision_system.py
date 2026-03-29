import requests
import numpy as np
from skyfield.api import load

# -----------------------------
# STEP 1 — Download fresh TLE
# -----------------------------
tle_urls = {
    "active": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
    "debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=fengyun-1c-debris&FORMAT=tle",
    "stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
}

for name, url in tle_urls.items():
    r = requests.get(url)
    open(f"{name}.txt", "w").write(r.text)

print("TLE updated ✔")

# -----------------------------
# STEP 2 — Load satellites
# -----------------------------
ts = load.timescale()
stations = load.tle_file("stations.txt")
active = load.tle_file("active.txt")
debris = load.tle_file("debris.txt")

satellites = stations + active[:50]   # start with 50 active satellites

print("Satellites:", len(satellites))
print("Debris:", len(debris))

# -----------------------------
# STEP 3 — Predict 7 days ahead
# -----------------------------
hours = np.linspace(0, 24*7, 500)
times = ts.utc(2026, 3, 28, hours)

ALERT_DISTANCE = 200  # km
alerts = []

for sat in satellites:
    pos_sat = sat.at(times).position.km
    for deb in debris:
        pos_deb = deb.at(times).position.km
        distances = np.linalg.norm(pos_sat - pos_deb, axis=0)
        min_dist = distances.min()

        if min_dist < ALERT_DISTANCE:
            alerts.append((sat.name, deb.name, round(min_dist,2)))

print("\n🚨 Collision alerts:", len(alerts))
for alert in alerts[:10]:
    print(alert)