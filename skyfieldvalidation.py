"""Cross-check ephemeris.csv (produced by emphemeris.py with SpiceyPy) against
an independent recomputation with Skyfield.

Both use the same DE440 data files, so this validates the code path (frame
handling, ENU construction, azimuth/elevation conventions), not the physics.
Expected agreement: well under 0.01 degrees.

Usage (from the project root, venv active, kernels downloaded):
    pip install skyfield
    python validate_skyfield.py [ephemeris.csv]
"""

import csv
import sys
import numpy as np
from skyfield.api import PlanetaryConstants, load

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "ephemeris.csv"
SITE_LAT, SITE_LON = 0.67, 23.3        # must match emphemeris.py
TOLERANCE_DEG = 0.01                   # pass/fail threshold

#lod kernels (same files as smp.tm)
ts = load.timescale()
eph = load("kernels/spk/de440s.bsp")
pc = PlanetaryConstants()
pc.read_text(load("kernels/fk/moon_de440_250416.tf"))
pc.read_text(load("kernels/pck/pck00011.tpc"))
pc.read_binary(load("kernels/pck/moon_pa_de440_200625.bpc"))

# Skyfield keeps only the LAST segment per frame when a .bpc has several.
# moon_pa_de440_200625.bpc has two (1550-2426 and 2426-2650); pick the one
# that covers the first timestamp in the CSV
with open(CSV_PATH, newline="") as f:
    rows = list(csv.DictReader(f))


def parse_utc(s):
    """'2000-02-20T12:00:00' -> (y, m, d, h, mi, s)"""
    d, t = s.split("T")
    y, mo, da = (int(x) for x in d.split("-"))
    h, mi, se = (float(x) for x in t.split(":"))
    return int(y), int(mo), int(da), int(h), int(mi), se


t0 = ts.utc(*parse_utc(rows[0]["utc"]))
for seg in pc._segment_list:
    if seg.initial_jd <= t0.tdb <= seg.final_jd:
        pc._segment_map[seg.body] = seg
        break

# The 'MOON_ME' name in the DE440 frame kernel is an alias; Skyfield needs the concrete frame it points to.
frame = pc.build_frame_named("MOON_ME_DE440_ME421")
site = eph["moon"] + pc.build_latlon_degrees(frame, SITE_LAT, SITE_LON)
sun, earth = eph["sun"], eph["earth"]

#recompute
max_diff = {"sun_az": 0.0, "sun_el": 0.0, "earth_az": 0.0, "earth_el": 0.0}
worst_row = {k: None for k in max_diff}


def angle_diff(a, b):
    """Smallest difference between two angles in degrees (handles 0/360)."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


for row in rows:
    t = ts.utc(*parse_utc(row["utc"]))
    obs = site.at(t)
    for name, body in (("sun", sun), ("earth", earth)):
        alt, az, _ = obs.observe(body).apparent().altaz()
        d_az = angle_diff(az.degrees, float(row[f"{name}_az"]))
        d_el = abs(alt.degrees - float(row[f"{name}_el"]))
        for key, d in ((f"{name}_az", d_az), (f"{name}_el", d_el)):
            if d > max_diff[key]:
                max_diff[key] = d
                worst_row[key] = row["utc"]

#report
print(f"Checked {len(rows)} rows of {CSV_PATH} against Skyfield")
print(f"Site: {SITE_LAT}N {SITE_LON}E   tolerance: {TOLERANCE_DEG} deg\n")
ok = True
for key in max_diff:
    flag = "OK " if max_diff[key] <= TOLERANCE_DEG else "FAIL"
    ok &= max_diff[key] <= TOLERANCE_DEG
    print(f"{flag}  {key:9s} max diff {max_diff[key]:.6f} deg  at {worst_row[key]}")
print("\nPASS" if ok else "\nFAIL")
sys.exit(0 if ok else 1)