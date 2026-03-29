from skyfield.api import load

ts = load.timescale()

satellites = load.tle_file('active.txt')

print("Total satellites :", len(satellites))

# On prend seulement 100 pour commencer
subset = satellites[:100]

print("Satellites utilisés :", len(subset))

for sat in subset[:5]:
    print(sat.name)