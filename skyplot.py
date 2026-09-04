import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

csv_path = "ephemeris.csv"

data = np.genfromtxt(csv_path, delimiter=',', names=True, dtype=None, encoding=None)

up = data["sun_el"] > 0
theta_up = np.radians(data["sun_az"][up])
r_up = 90 - data["sun_el"][up]

# Full-length arrays, night included, so the Sun dot can vanish below the rim.
theta_all = np.radians(data["sun_az"])
r_all = 90 - data["sun_el"]
utc = data["utc"]

fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
ax.set_theta_zero_location("N")   # 0° at top
ax.set_theta_direction(-1)        # clockwise, so 90° = East on the right
ax.set_rlim(0, 90)                # rim = horizon

ax.plot(theta_up, r_up, marker=".", linestyle="", markersize=1, color="orange", alpha=0.4, label="Sun path")

ax.scatter(np.radians(data["earth_az"]), 90 - data["earth_el"],
           s=4, color="tab:blue", label="Earth")

ax.set_yticks([0, 30, 60, 90])
ax.set_yticklabels(["90°", "60°", "30°", "0°"])   # show elevation, not zenith distance
ax.set_title("Sky at 0.67°N 23.3°E, Feb 2000")
ax.legend(loc="lower right")

sun_dot, = ax.plot([], [], "o", color="orange", markersize=10, label="Sun")
label = ax.text(0.02, 0.95, "", transform=ax.transAxes)

frames = range(0, len(utc), 3)   # every 3rd row keeps the GIF under ~12s at 20fps


def update(i):
    sun_dot.set_data([theta_all[i]], [r_all[i]])
    label.set_text(f"{utc[i]}  el={data['sun_el'][i]:.1f}°")
    return sun_dot, label


anim = FuncAnimation(fig, update, frames=frames, interval=50, blit=True)

plt.savefig("skyplot.png", dpi=150)
anim.save("skyplot.gif", writer="pillow", fps=20)
plt.show()