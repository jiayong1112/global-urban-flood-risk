# -*- coding: utf-8 -*-
"""Where every script reads its inputs and writes its outputs.

Paths are resolved relative to the repository, so a fresh clone works without
editing any script. Three roots:

  data/     Tables deposited with this repository. Tracked in git. These are
            the outputs used for the manuscript, so the figure scripts run
            from a clone with no Earth Engine access at all.

  exports/  Earth Engine exports, which are too large to redistribute and are
            not tracked. Run the `gee/*Export*.js` scripts and drop the CSVs
            here, in the subdirectories named below. Override the location
            with the GUFR_EXPORTS environment variable if the files already
            live somewhere else.

  output/   Everything the scripts generate: figures and regenerated tables.
            Not tracked, created on demand. Override with GUFR_OUTPUT.

`table()` is the reason a clone is useful on its own: it prefers a table you
have just regenerated in output/, and falls back to the deposited copy in
data/. So `fig3_boxplots_2026-08.py` draws the published figure immediately
after cloning, and redraws it from your own numbers once you have re-run
`a5_assemble_2026-08.py`.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = Path(os.environ.get("GUFR_DATA", ROOT / "data"))
EXPORTS = Path(os.environ.get("GUFR_EXPORTS", ROOT / "exports"))
OUTPUT = Path(os.environ.get("GUFR_OUTPUT", ROOT / "output"))

# --- Earth Engine export subdirectories -------------------------------------
# Produced by, respectively:
#   fuaExport_Jan2026.js            (also the WSF3D and GBH2020 height variants)
#   fuaExport_2026-08.js
#   fuaExport_GDP_2026-08.js
#   STAGE2*_diagnostics_fuaExport_2026-08.js
#   fig4_export_Jul2026.js
FUA_2026_01 = EXPORTS / "csv_fua_2026-1-17"
FUA_2026_08 = EXPORTS / "flood_fua_2026-08"
FUA_GDP_2026_08 = EXPORTS / "flood_fua_GDP_2026-08"
DIAG_2026_08 = EXPORTS / "csv_fua_diag_2026-08"
FIG4_TIFFS = EXPORTS / "fig4_tiffs_2026-7"

# Deposited inputs that are small enough to ship.
TOTAL_GDP_CSV = DATA / "fua_totalGDP_2026-7.csv"

# Natural Earth 1:110m country polygons, used as the basemap for the tertile
# maps. Not redistributed: download the shapefile from naturalearthdata.com and
# unzip it into exports/ne_110m_admin_0_countries/.
NATURAL_EARTH = EXPORTS / "ne_110m_admin_0_countries" / "ne_110m_admin_0_countries.shp"

_HINTS = {
    FUA_2026_01: "run gee/fuaExport_Jan2026.js",
    FUA_2026_08: "run gee/fuaExport_2026-08.js",
    FUA_GDP_2026_08: "run gee/fuaExport_GDP_2026-08.js",
    DIAG_2026_08: "run gee/STAGE1*_diagnostics_toAsset_2026-08.js then "
                  "gee/STAGE2*_diagnostics_fuaExport_2026-08.js",
    FIG4_TIFFS: "run gee/fig4_export_Jul2026.js",
    NATURAL_EARTH: "download the Natural Earth 1:110m admin-0 countries "
                   "shapefile from naturalearthdata.com",
}


def need(path):
    """Return `path`, or explain precisely what is missing and how to get it."""
    if path.exists():
        return path
    hint = _HINTS.get(path, "see the script header for what belongs here")
    raise FileNotFoundError(
        f"missing input: {path}\n"
        f"  To obtain it: {hint}, then put it at the path above.\n"
        f"  Large inputs are not redistributed with this repository.\n"
        f"  If you already hold them elsewhere, point GUFR_EXPORTS at that "
        f"directory."
    )


def table(name):
    """Locate a summary table, preferring a freshly regenerated copy.

    Looks in output/ first, then in the deposited data/. Raises with both
    locations named if neither has it.
    """
    for root in (OUTPUT, DATA):
        candidate = root / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"missing table: {name}\n"
        f"  looked in {OUTPUT} and {DATA}.\n"
        f"  Regenerate it with the script that produces it, or check that the "
        f"deposited copy is present in data/."
    )


def out(*parts):
    """A path under output/, creating the directory it lives in."""
    p = OUTPUT.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


if __name__ == "__main__":
    print(f"repository root : {ROOT}")
    for label, path in (("deposited data", DATA), ("GEE exports", EXPORTS),
                        ("generated output", OUTPUT)):
        print(f"{label:16s}: {path}  {'[present]' if path.exists() else '[absent]'}")
    print("\nEarth Engine export subdirectories:")
    for path in (FUA_2026_01, FUA_2026_08, FUA_GDP_2026_08, DIAG_2026_08,
                 FIG4_TIFFS):
        n = len(list(path.glob("*"))) if path.exists() else 0
        state = f"[{n} files]" if path.exists() else "[absent]"
        print(f"  {path.name:24s} {state}")
