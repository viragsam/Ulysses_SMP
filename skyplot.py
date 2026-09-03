import matplotlib.pyplot as plt
import numpy as np

csv_path = "ephemeris.csv"

data = np.genfromtxt(csv_path, delimiter=',', names=True, dtype=None, encoding=None)

up = data["sun_el"] > 0
theta = np.radians(data["sun_az"][up])
r = 90 - data["sun_el"][up]

fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
ax.set_theta_zero_location("N")   # 0° at top
ax.set_theta_direction(-1)        # clockwise, so 90° = East on the right
ax.set_rlim(0, 90)                # rim = horizon

ax.plot(theta, r, marker=".", linestyle="", markersize=1, color="orange", label="Sun")

ax.scatter(np.radians(data["earth_az"]), 90 - data["earth_el"],
           s=4, color="tab:blue", label="Earth")

ax.set_yticks([0, 30, 60, 90])
ax.set_yticklabels(["90°", "60°", "30°", "0°"])   # show elevation, not zenith distance
ax.set_title("Sky at 0.67°N 23.3°E, Feb 2000")
ax.legend(loc="lower right")

plt.savefig("skyplot.png", dpi=150)
plt.show()