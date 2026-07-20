# 🛰 AstroZeka — Space Debris Detection & Collision Screening

AstroZeka has two independent subsystems that both feed into the same goal
(spotting dangerous debris early):

| Subsystem | Status | What it does |
|---|---|---|
| **`orbital/`** | ✅ Working, real data | Downloads TLEs from CelesTrak, propagates orbits with SGP4 (via [Skyfield](https://rhodesmill.org/skyfield/)), and screens for close approaches between satellites and known debris fields. |
| **`vision/`** | 🔧 Scaffold only | YOLOv8 + OpenCV pipeline meant to detect debris/satellites in optical imagery. The code now runs without crashing, but there is **no labeled training data yet**, so the detector has nothing debris-specific to find until you add one. |

Your original README described AstroZeka as a computer-vision project
(PyTorch/YOLOv8/OpenCV), but the scripts you'd actually written and had
working end-to-end were the orbital TLE ones. This project keeps both,
clearly labeled, so nothing is oversold.

---

## Project structure

```
astrozeka/
├── config.py                  # All shared constants: URLs, thresholds, paths
├── main.py                    # CLI entry point for the orbital pipeline
├── requirements.txt
├── data/
│   ├── tle/                   # Downloaded TLE files (*.txt)
│   └── cv/dataset/            # YOLO-format image/label folders (empty — add your own)
├── orbital/
│   ├── tle_manager.py         # Download + load TLE groups from CelesTrak
│   ├── collision_detector.py  # Core conjunction-screening engine
│   ├── report.py              # Console table + CSV export
│   └── visualizer.py          # 3D orbit plot (Plotly, saved to HTML)
├── vision/
│   ├── dataset.yaml           # YOLO dataset config
│   ├── train.py                # Fine-tune YOLOv8 on your labeled data
│   ├── detect_batch.py         # Run a trained model over a folder of images
│   └── detect_webcam.py        # Live webcam detection
└── outputs/                   # Generated reports, CSVs, HTML plots (created at runtime)
```

---

## Quick start (orbital screening)

```bash
pip install -r requirements.txt

# Screen the ISS/stations group against Fengyun-1C debris, 7 days ahead,
# using data already in this folder:
python main.py

# Fresh download from CelesTrak, tighter 10 km threshold, only 3 days out,
# and render a 3D plot of the single closest conjunction:
python main.py --download --alert-distance 10 --days 3 --visualize-top

# Screen every primary group against every debris group in one go:
python main.py --full --alert-distance 25

# Or pick specific groups yourself:
python main.py --primary-groups stations oneweb kuiper \
                --debris-groups fengyun_debris cosmos_debris iridium_debris
```

> **Heads up on `--full`:** it includes `active` (~15,000 objects) and
> `starlink` (~10,000 objects) as primaries. Screening those against every
> debris group means tens of millions of orbit-pair comparisons and can
> take a long time on a laptop. For a fast, still-meaningful run, use
> `--primary-groups stations oneweb kuiper` (which is what the results
> below are from) rather than the full mega-constellations.

Output:
- A ranked table printed to the console (closest conjunction first).
- `outputs/conjunctions.csv` — every event found, for further analysis.
- `outputs/summary.html` — a dark-themed, self-contained report: a
  horizontal bar chart of the closest conjunctions color-scaled by risk
  (red = closest/riskiest, blue = near the threshold), plus the alert
  threshold marked as a reference line. This is the file to actually hand
  to someone — the CSV is for digging further.
- Optionally `outputs/closest_conjunction.html` (`--visualize-top`) — an
  interactive 3D plot of the single closest pair's orbits, with the actual
  point of closest approach marked and labeled with live distance/time,
  and a dashed "miss vector" line between the two objects at that instant.

### What actually changed from your original scripts

Your original `astrozeka_collision_system.py`, `collision_alert.py`, and
`predict_orbit.py` all screened a **hardcoded window starting March 28,
2026** (`ts.utc(2026, 3, 28, hours)`), no matter when you ran them. That
means the "alerts" they printed were for a fixed date in the past/future,
not "the next 7 days" as advertised. `collision_detector.py` now defaults
to `ts.now()` and screens forward from whenever you actually run it.

Other fixes worth knowing about:
- **Alert distance was inconsistent** (200 km in one script, 50 km in
  another) with no shared source of truth — now one setting in
  `config.py`, overridable via `--alert-distance`.
- **200 km is a very loose threshold.** Real conjunction screening
  typically flags tens of km for a closer look, since TLE propagation
  error alone can be kilometers. Default here is 25 km; treat any of this
  as a coarse screen, not a certified collision probability — proper risk
  assessment needs covariance data this pipeline doesn't have.
- **Debris positions were recomputed for every primary** in a nested loop;
  now computed once per debris object and reused.
- **No results were saved anywhere** — everything printed to stdout and
  vanished. Now written to CSV every run.
- **`fig.show()`** in the visualizer only works with a local interactive
  renderer/notebook; in a script/server context it silently did nothing.
  Now it always writes an HTML file, with `fig.show()` as an opt-in extra.

---

## Vision subsystem (optical debris detection)

This part is a **scaffold**, not a working detector yet:

1. `vision/train.py` — fine-tunes a YOLOv8 checkpoint on `vision/dataset.yaml`.
   **You need to populate `data/cv/dataset/images/{train,val}/` with your
   own labeled images and matching YOLO-format label files in
   `data/cv/dataset/labels/{train,val}/` before this will learn anything
   useful.** Right now those folders are empty placeholders.
2. `vision/detect_batch.py` — runs a trained checkpoint over a folder of
   images and saves annotated copies.
3. `vision/detect_webcam.py` — same, but live from a webcam.

Bugs fixed here (details in each file's docstring):
- `detect_webcam.py` (was `detect.py`) — the original file's contents were
  a shell heredoc (`cat > ... << 'EOF' ... EOF`) pasted *around* the Python
  code, so it wasn't valid Python and would raise a `SyntaxError` if run.
- `train.py` (was `train_detector.py`) — called `model.train(...)` on a
  `model` that was never created, and its config was a bare `...`
  placeholder with no dataset path or hyperparameters.
- `detect_batch.py` (was `detect_cv.py`) — used `cv2.imshow`/`waitKey(0)`,
  which requires an interactive display and does nothing headless; now
  always saves annotated images to `outputs/detections/` and only opens a
  window if you pass `--show`.

**Where to get labeled debris imagery**, since none exists in this repo:
optical debris-tracking datasets are uncommon publicly, but ground-based
observatories (e.g. Space Surveillance Telescope programs) and simulated
renders (e.g. from orbital scenes in Blender/STK) are the usual starting
points. That data-sourcing step is the actual bottleneck for this
subsystem, more than the code.

---

## Honest limitations

- TLE-based propagation (SGP4) has inherent error that grows with time
  since the TLE's epoch — a "collision" flagged 7 days out is far less
  certain than one flagged 6 hours out.
- This is a **screening** tool: it estimates miss distance from mean
  orbital elements. It is not a substitute for operator-grade conjunction
  data messages (CDMs) with real covariance, which is what actual
  maneuver decisions are based on.
- The vision subsystem has no trained weights and no labeled dataset
  included — it's wired up correctly but needs real data to be useful.
