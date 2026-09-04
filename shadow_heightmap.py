import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

csv_path = sys.argv[1] if len(sys.argv) > 1 else "ephemeris.csv"
gif_path = sys.argv[2] if len(sys.argv) > 2 else "shadow_heightmap.gif"

data = np.genfromtxt(csv_path, delimiter=',', names=True, dtype=None, encoding=None)
az = np.radians(data["sun_az"])
el = data["sun_el"]
utc = data["utc"]

# --- synthetic crater heightmap: a bowl with a raised rim, cell units = 1 ---
N = 60
X, Y = np.meshgrid(np.arange(N), np.arange(N))
R = np.hypot(X - N / 2, Y - N / 2)
crater_r, rim_r, depth, rim_h = N * 0.3, N * 0.35, 8.0, 4.0
heightmap = -depth * np.clip(1 - (R / crater_r) ** 2, 0, None)
heightmap += rim_h * np.exp(-((R - rim_r) / (N * 0.06)) ** 2)


def shadow_mask(sun_az, sun_el):
    """Horizon shadowing: march every cell toward the sun; it's shadowed if
    any intervening cell pokes above the sun ray's height at that distance."""
    if sun_el <= 0:
        return np.ones_like(heightmap, dtype=bool)
    dx, dy = np.sin(sun_az), np.cos(sun_az)
    tan_el = np.tan(np.radians(sun_el))
    blocked = np.zeros_like(heightmap, dtype=bool)
    for d in range(1, int(np.hypot(N, N)) + 1):
        Xi, Yi = X + dx * d, Y + dy * d
        in_bounds = (Xi >= 0) & (Xi < N) & (Yi >= 0) & (Yi < N)
        sample_h = heightmap[np.clip(Yi.round().astype(int), 0, N - 1),
                              np.clip(Xi.round().astype(int), 0, N - 1)]
        blocked |= in_bounds & (sample_h > heightmap + d * tan_el)
    return blocked


fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 5))

ax.imshow(heightmap, cmap="terrain", origin="lower")
ax.set_title(f"Synthetic crater ({csv_path})")
overlay = ax.imshow(np.zeros((N, N, 4)), origin="lower")   # RGBA shadow layer
label = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", color="white")

# Illumination map: fraction of rows each cell is lit over the whole CSV,
# computed once up front rather than accumulated frame-by-frame in update().
lit_fraction = np.zeros_like(heightmap)
for i in range(len(utc)):
    lit_fraction += ~shadow_mask(az[i], el[i])
lit_fraction /= len(utc)

im2 = ax2.imshow(lit_fraction, cmap="inferno", origin="lower", vmin=0, vmax=1)
ax2.set_title("% of time lit (whole CSV)")
fig.colorbar(im2, ax=ax2, label="fraction lit")

frames = range(0, len(utc), 3)   # every 3rd row keeps the GIF under ~12s at 20fps


def update(i):
    mask = shadow_mask(az[i], el[i])
    rgba = np.zeros((N, N, 4))
    rgba[..., 3] = np.where(mask, 0.65, 0.0)   # opaque dark where shadowed
    overlay.set_data(rgba)
    label.set_text(f"{utc[i]}  el={el[i]:.1f}°")
    return overlay, label


anim = FuncAnimation(fig, update, frames=frames, interval=50, blit=True)

anim.save(gif_path, writer="pillow", fps=20)
plt.savefig("illumination_map.png", dpi=150)
plt.show()
