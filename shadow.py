import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

csv_path = sys.argv[1] if len(sys.argv) > 1 else "ephemeris.csv"
gif_path = sys.argv[2] if len(sys.argv) > 2 else "shadow.gif"

data = np.genfromtxt(csv_path, delimiter=',', names=True, dtype=None, encoding=None)

az = np.radians(data["sun_az"])
el = data["sun_el"]
utc = data["utc"]
hours = np.arange(len(utc))   # one row per hour in this CSV

h = 1.0          # block height, in shadow-length units
L_max = 50 * h    # clamp so the plot doesn't explode near sunrise/sunset
L_all = np.where(el > 0, np.minimum(h / np.tan(np.radians(np.clip(el, 1e-3, None))), L_max), np.nan)

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 5))

ax.set_xlim(-L_max - 5, L_max + 5)
ax.set_ylim(-L_max - 5, L_max + 5)
ax.set_aspect("equal")
ax.set_xlabel("east →")
ax.set_ylabel("north →")
ax.set_title(f"Shadow of a unit block ({csv_path})")

ax.add_patch(plt.Rectangle((-0.5, -0.5), 1, 1, color="tab:gray"))

shadow_line, = ax.plot([], [], "-", color="black", linewidth=2)
label = ax.text(0.02, 0.95, "", transform=ax.transAxes)

# Second panel: shadow length over the whole month, so the short-shadow
# midday hours are still readable even though the polar plot clamps them.
ax2.plot(hours, L_all, color="black", linewidth=0.8)
ax2.set_ylim(0, L_max)
ax2.set_xlabel("hours since start")
ax2.set_ylabel("shadow length L")
ax2.set_title("L vs time")
time_marker, = ax2.plot([], [], "o", color="orange", markersize=6)

frames = range(0, len(utc), 3)   # every 3rd row keeps the GIF under ~12s at 20fps


def update(i):
    if el[i] > 0:
        L = L_all[i]
        dx = -L * np.sin(az[i])
        dy = -L * np.cos(az[i])
        shadow_line.set_data([0, dx], [0, dy])
    else:
        shadow_line.set_data([], [])   # sun below horizon, no shadow
    label.set_text(f"{utc[i]}  el={el[i]:.1f}°")
    time_marker.set_data([hours[i]], [L_all[i]])
    return shadow_line, label, time_marker


anim = FuncAnimation(fig, update, frames=frames, interval=50, blit=True)

anim.save(gif_path, writer="pillow", fps=20)
plt.show()
