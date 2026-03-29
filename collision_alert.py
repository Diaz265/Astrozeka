import numpy as np
from skyfield.api import load

ts = load.timescale()
stations = load.tle_file('stations.txt')
debris = load.tle_file('fengyun_debris.txt')

hours = np.linspace(0, 24, 100)
times = ts.utc(2026, 3, 28, hours)

ALERT_DISTANCE = 50  # km
alerts = []

for sat in stations:
    pos_sat = sat.at(times).position.km
    for deb in debris:
        pos_deb = deb.at(times).position.km
        distances = np.linalg.norm(pos_sat - pos_deb, axis=0)
        min_dist = distances.min()

        if min_dist < ALERT_DISTANCE:
            alerts.append((sat.name, deb.name, round(min_dist, 2)))

print("Collision alerts in next 24h:")
print("Total alerts:", len(alerts))

for alert in alerts[:10]:
    print(alert)