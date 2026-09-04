"""Shared crater heightmap + horizon-shadowing logic for shadow_heightmap.py
and illumination_compare.py, so both animate/compare the same terrain."""

import numpy as np

N_DEFAULT = 60


def synthetic_crater(n=N_DEFAULT):
    """Bowl + raised rim, cell units = 1."""
    X, Y = np.meshgrid(np.arange(n), np.arange(n))
    R = np.hypot(X - n / 2, Y - n / 2)
    crater_r, rim_r, depth, rim_h = n * 0.3, n * 0.35, 8.0, 4.0
    h = -depth * np.clip(1 - (R / crater_r) ** 2, 0, None)
    h += rim_h * np.exp(-((R - rim_r) / (n * 0.06)) ** 2)
    return h


def load_lola_crop(path, size=100):
    """Load a cropped LOLA GeoTIFF and downsample it to `size` x `size`
    cells (nearest-neighbor decimation, adequate for this demo).

    GeoTIFF row 0 is the northernmost row, but shadow_mask treats +row as
    +north (dy = cos(az)), so the array is flipped. Heights come back in
    metres and pixel spacing in metres/pixel; shadow_mask's `d` is in cell
    units, so heights are rescaled by (pixel spacing * downsample step) to
    match — otherwise a 100 m-tall crater at 20 m/px would cast a shadow as
    if it were 100 cells tall instead of ~5.

    Only equirectangular tiles are handled correctly. LOLA's polar-stereographic
    products need azimuth remapped per-longitude before this applies.
    """
    import rasterio
    with rasterio.open(path) as src:
        arr = src.read(1).astype(float)
        px_size = src.res[0]   # metres per pixel, assumed square
    arr = arr[::-1]             # row 0 = north -> +row index = +north
    step = max(arr.shape[0] // size, arr.shape[1] // size, 1)
    arr = arr[::step, ::step][:size, :size]
    return arr / (px_size * step)   # metres -> cell units (1 cell = step pixels)


def shadow_mask(heightmap, sun_az, sun_el):
    """Horizon shadowing: march every cell toward the sun; it's shadowed if
    any intervening cell pokes above the sun ray's height at that distance."""
    n = heightmap.shape[0]
    if sun_el <= 0:
        return np.ones_like(heightmap, dtype=bool)
    X, Y = np.meshgrid(np.arange(n), np.arange(n))
    dx, dy = np.sin(sun_az), np.cos(sun_az)
    tan_el = np.tan(np.radians(sun_el))
    blocked = np.zeros_like(heightmap, dtype=bool)
    for d in range(1, int(np.hypot(n, n)) + 1):
        Xi, Yi = X + dx * d, Y + dy * d
        in_bounds = (Xi >= 0) & (Xi < n) & (Yi >= 0) & (Yi < n)
        sample_h = heightmap[np.clip(Yi.round().astype(int), 0, n - 1),
                              np.clip(Xi.round().astype(int), 0, n - 1)]
        blocked |= in_bounds & (sample_h > heightmap + d * tan_el)
    return blocked


def illumination_map(heightmap, az, el):
    """Fraction of the (az, el) rows each cell is lit."""
    lit = np.zeros_like(heightmap)
    for a, e in zip(az, el):
        lit += ~shadow_mask(heightmap, a, e)
    return lit / len(az)
