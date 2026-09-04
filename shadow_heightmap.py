import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from heightmap import synthetic_crater, load_lola_crop, shadow_mask, illumination_map

csv_path = sys.argv[1] if len(sys.argv) > 1 else "ephemeris.csv"
gif_path = sys.argv[2] if len(sys.argv) > 2 else "shadow_heightmap.gif"
dem_path = sys.argv[3] if len(sys.argv) > 3 else None   # cropped LOLA GeoTIFF; omit for the synthetic crater

data = np.genfromtxt(csv_path, delimiter=',', names=True, dtype=None, encoding=None)
az = np.radians(data["sun_az"])
el = data["sun_el"]
utc = data["utc"]

heightmap = load_lola_crop(dem_path) if dem_path else synthetic_crater()
N = heightmap.shape[0]

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 5))

ax.imshow(heightmap, cmap="terrain", origin="lower")
ax.set_title(f"Terrain ({dem_path or 'synthetic crater'})")
overlay = ax.imshow(np.zeros((N, N, 4)), origin="lower")   # RGBA shadow layer
label = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", color="white")

# Illumination map: fraction of rows each cell is lit over the whole CSV,
# computed once up front rather than accumulated frame-by-frame in update().
lit_fraction = illumination_map(heightmap, az, el)

im2 = ax2.imshow(lit_fraction, cmap="inferno", origin="lower", vmin=0, vmax=1)
ax2.set_title(f"% of time lit ({csv_path})")
fig.colorbar(im2, ax=ax2, label="fraction lit")

frames = range(0, len(utc), 3)   # every 3rd row keeps the GIF under ~12s at 20fps


def update(i):
    mask = shadow_mask(heightmap, az[i], el[i])
    rgba = np.zeros((N, N, 4))
    rgba[..., 3] = np.where(mask, 0.65, 0.0)   # opaque dark where shadowed
    overlay.set_data(rgba)
    label.set_text(f"{utc[i]}  el={el[i]:.1f}°")
    return overlay, label


anim = FuncAnimation(fig, update, frames=frames, interval=50, blit=True)

anim.save(gif_path, writer="pillow", fps=20)
plt.savefig("illumination_map.png", dpi=150)
plt.show()
