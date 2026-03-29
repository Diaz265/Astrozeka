import requests

tle_urls = {
    "active": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
    "stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
    "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
    "oneweb": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle",
    "kuiper": "https://celestrak.org/NORAD/elements/gp.php?GROUP=kuiper&FORMAT=tle",
    "iridium_debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle",
    "cosmos_debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle",
    "fengyun_debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=fengyun-1c-debris&FORMAT=tle"
}

for name, url in tle_urls.items():
    print(f"Downloading {name}...")
    response = requests.get(url)
    
    with open(f"{name}.txt", "w") as f:
        f.write(response.text)

print("All TLE files downloaded 🚀")