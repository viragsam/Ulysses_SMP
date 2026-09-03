# Emphemeris generator for a lunar site. Outputs a CSV with azimuth and elevation of the Sun and Earth over a time range
import spiceypy
import numpy as np
import csv
from numpy.linalg import norm
spiceypy.furnsh("smp.tm") # Hand the kernels to SP

# Time range inputs
start = input("Enter start UTC (YYYY-MM-DDTHH:MM:SS): ")
stop = input("Enter stop UTC (YYYY-MM-DDTHH:MM:SS): ")
step_s = input("Enter step seconds (default 3600): ")
if step_s.strip() == "":
	step = 3600
else:
	step = float(step_s)

et0 = spiceypy.str2et(start)
et1 = spiceypy.str2et(stop)

def az_el(target, et, site, up, east, north):
	"""Return azimuth (deg, 0..360 compass) and elevation (deg) for a target.

	`up`, `east`, `north` are required and should be precomputed by the
	caller to avoid hidden recomputation paths.
	"""
	vec, _ = spiceypy.spkpos(target, et, "MOON_ME", "LT+S", "MOON")
	tgt_from_site = vec - site

	tgt_enu = np.array([
		np.dot(tgt_from_site, east),
		np.dot(tgt_from_site, north),
		np.dot(tgt_from_site, up),
	])
	elevation = np.arcsin(tgt_enu[2] / np.linalg.norm(tgt_enu))
	azimuth = np.arctan2(tgt_enu[0], tgt_enu[1])
	az_deg = (azimuth * spiceypy.dpr()) % 360
	return az_deg, elevation * spiceypy.dpr()


# Site definition (compute once)
site_lon = 23.3 * spiceypy.rpd()  # radians
site_lat = 0.67 * spiceypy.rpd()  # radians
site = spiceypy.latrec(1737.4, site_lon, site_lat)
up = site / norm(site)
east = np.cross([0, 0, 1], up)
east = east / norm(east)
north = np.cross(up, east)

#oop over the time range and write CSV with SUN and EARTH az/el
out_path = "ephemeris.csv"
with open(out_path, "w", newline="") as csvfile:
	writer = csv.writer(csvfile)
	writer.writerow(["utc", "sun_az", "sun_el", "earth_az", "earth_el"])
	et = et0
	while et <= et1:
		sun_az, sun_el = az_el("SUN", et, site, up, east, north)
		earth_az, earth_el = az_el("EARTH", et, site, up, east, north)
		ts = spiceypy.et2utc(et, "ISOC", 0)
		writer.writerow([
			ts,
			f"{sun_az:.4f}",
			f"{sun_el:.4f}",
			f"{earth_az:.4f}",
			f"{earth_el:.4f}",
		])
		et += step
print(f"Wrote {out_path}")
