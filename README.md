# SMP Ephemeris Prototype

Python reference implementation of the Sun/Earth position calculation for the
ULYSSES Strategic Mission Planner rebuild. Produces a table of Sun and Earth
azimuth/elevation as seen from a point on the lunar surface over a time range.
Its purpose is to validate the geometry before it is reimplemented in Unreal
(via MaxQ/SPICE) and to serve as a test fixture for that implementation.

## Files

| File | Purpose |
|---|---|
| `emphemeris.py` | The script. Prompts for start, stop and step; writes `ephemeris.csv`. |
| `smp.tm` | SPICE meta-kernel: a list of the data files to load. |
| `get_kernels.sh` / `get_kernels.ps1` | Download the kernels (Linux/macOS and Windows). |
| `kernels/` | NAIF data files (not code). See below. |
| `ephemeris.csv` | Output: `utc, sun_az, sun_el, earth_az, earth_el`, one row per step. |

## Kernels

SPICE is only math; all data comes from kernel files downloaded from
`https://naif.jpl.nasa.gov/pub/naif/generic_kernels/`.

| File | Type | Provides |
|---|---|---|
| `lsk/naif0012.tls` | leap seconds | UTC to ephemeris time conversion |
| `spk/de440s.bsp` | SPK | positions of Sun, Earth, Moon (DE440, 1849–2150) |
| `pck/pck00011.tpc` | text PCK | body radii and approximate rotation |
| `pck/moon_pa_de440_200625.bpc` | binary PCK | precise lunar orientation from DE440 |
| `fk/moon_de440_250416.tf` | frame kernel | defines the `MOON_ME` body-fixed frame |

`MOON_ME` (Mean Earth / Polar Axis) is the frame used by LOLA DEMs, so
directions computed here line up with the terrain data.

## How it works

1. `furnsh("smp.tm")` loads all kernels.
2. `str2et()` converts the UTC string to ephemeris time (seconds past J2000).
3. `spkpos("SUN", et, "MOON_ME", "LT+S", "MOON")` returns the Sun's position
   relative to the Moon's centre, in the Moon's body-fixed frame (km).
   Same call with `"EARTH"` for earthshine.
4. The site (currently hard-coded: 0.67°N, 23.3°E, radius 1737.4 km) is turned
   into a surface vector with `latrec()`.
5. A local East/North/Up frame is built at the site:
   `up = site/|site|`, `east = normalize(z × up)`, `north = up × east`.
6. The target vector is moved to originate at the site (`vec - site`),
   projected onto E/N/U, then
   `el = asin(U/|v|)`, `az = atan2(E, N)` mapped to 0–360° clockwise from north.
7. Steps 3–6 repeat for each time step; results are written to CSV.

Note: the `east` construction fails exactly at the poles (cross product is
zero). Fine for equatorial sites; handle separately for polar missions.

## Validation

Run: 2000-02-01 to 2000-03-01, 1 h step, site 0.67°N 23.3°E (698 rows).

| Check | Expected | Result |
|---|---|---|
| Sun vector length, early Feb | slightly under 1 AU | 147.1 million km |
| Subsolar latitude | within ±1.5° (lunar axial tilt) | −0.32° |
| Subsolar longitude drift | ~12.2°/day, 180° in 15 days | 176.5° on 5 Feb, −6.0° on 20 Feb |
| Single-instant check, 2000-02-20 12:00 | Sun 29.3° past local noon, el ≈ 60.7°, az west | el 60.67°, az 267.2° |
| Sunrise/sunset count over one month | one each, ~14.8 days apart | rise 10 Feb 17:00, set 25 Feb 12:00 |
| Noon peak elevation | near 90° (site near equator) | 88.6° on 18 Feb |
| Earth elevation | roughly constant ~64° with libration wobble | 60.2°–71.1° |
| Earth azimuth | western sky (site is 23° east of sub-Earth point) | 247°–283° |

All checks consistent with expected lunar geometry.

Not yet done: comparison of one instant against JPL Horizons
(Observer Table, target Sun, observer on Moon at site coordinates) to confirm
the azimuth zero-point to sub-0.1°.

## Setup

Requires Python 3.10+ and ~45 MB of kernel downloads.

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install spiceypy numpy
chmod +x get_kernels.sh
./get_kernels.sh
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install spiceypy numpy
Set-ExecutionPolicy -Scope Process Bypass
.\get_kernels.ps1
```

Both download scripts are idempotent (existing files are skipped). If you
prefer to fetch manually, the URLs are:

```
https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls
https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp
https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc
https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de440_200625.bpc
https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_de440_250416.tf
```

Place them under `kernels/lsk`, `kernels/spk`, `kernels/pck`, `kernels/fk`
as listed in `smp.tm`. NAIF occasionally updates the frame kernel; if the
`.tf` download 404s, browse `fk/satellites/` for the newest `moon_de440_*.tf`
and update both the script and `smp.tm`.

## Usage

```bash
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
python emphemeris.py
# Enter start UTC (YYYY-MM-DDTHH:MM:SS): 2000-02-01T00:00:00
# Enter stop UTC  (YYYY-MM-DDTHH:MM:SS): 2000-03-01T00:00:00
# Enter step seconds (default 3600):
```

Run from the project root so the relative kernel paths in `smp.tm` resolve.

## Next

- Horizons cross-check (see above).
- Reimplement steps 3–6 in Unreal with the MaxQ plugin (same function names:
  `spkpos`, `latrec`); diff its output against `ephemeris.csv`.
