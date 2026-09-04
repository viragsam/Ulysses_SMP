import sys

import matplotlib.pyplot as plt
import numpy as np

from heightmap import synthetic_crater, illumination_map

eq_path = sys.argv[1] if len(sys.argv) > 1 else "ephemeris.csv"
polar_path = sys.argv[2] if len(sys.argv) > 2 else "ephemeris_polar.csv"

heightmap = synthetic_crater()
N = heightmap.shape[0]
cy = cx = N // 2

fig, axes = plt.subplots(1, 2, figsize=(10, 5))
titles = ["Equatorial, 0.67°N 23.3°E", "Polar, 85°S 23.3°E"]

for ax, csv_path, title in zip(axes, [eq_path, polar_path], titles):
    data = np.genfromtxt(csv_path, delimiter=',', names=True, dtype=None, encoding=None)
    az = np.radians(data["sun_az"])
    el = data["sun_el"]
    lit = illumination_map(heightmap, az, el)
    im = ax.imshow(lit, cmap="inferno", origin="lower", vmin=0, vmax=1)
    ax.set_title(f"{title}\nfloor lit {lit[cy, cx] * 100:.0f}%")

fig.colorbar(im, ax=axes, label="fraction lit", shrink=0.8)
fig.suptitle("Same synthetic crater, same month, different site latitude")

plt.savefig("illumination_compare.png", dpi=150)
plt.show()
