"""
Figure 2 (Jul 2026 revision): country-level FD-AED vs IR-AED tertile maps.

Reviewer request: replace the green/yellow/red categorical scheme with a
sequential, colorblind-friendly light-to-dark palette (ColorBrewer YlOrRd 3-class).

Tertiles are computed over the 105 countries with positive values for both metrics
in fua_world_countries_2026-1-8.csv (FUA-aggregated, JRC building heights).
Countries without data are shown in light gray.
Basemap: Natural Earth 110m admin_0_countries, Mollweide projection.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
CTY_CSV = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission" / "fua_world_countries_2026-1-8.csv"
SHP = BASE / "data" / "ne_110m_admin_0_countries" / "ne_110m_admin_0_countries.shp"
OUT_DIR = BASE / "figures"

# ColorBrewer YlOrRd 3-class (sequential, CVD-safe) + no-data gray
TERTILE_COLORS = ["#ffeda0", "#feb24c", "#f03b20"]
NODATA = "#d9d9d9"
LABELS = ["Low (bottom third)", "Medium (middle third)", "High (top third)"]

# dataset country_na (concatenated) -> Natural Earth ADMIN name
NAME_TO_NE = {
    "UnitedStates": "United States of America", "UnitedKingdom": "United Kingdom",
    "UnitedKingdom(Scotland)": "United Kingdom", "CzechRepublic": "Czechia",
    "SouthKorea": "South Korea", "NorthKorea": "North Korea",
    "SouthAfrica": "South Africa", "SaudiArabia": "Saudi Arabia",
    "SriLanka": "Sri Lanka", "NewZealand": "New Zealand",
    "BurkinaFaso": "Burkina Faso", "CotedIvoire": "Ivory Coast",
    "Congo(DRC)": "Democratic Republic of the Congo",
    "RepublicofCongo": "Republic of the Congo",
    "DemocraticRepublicoftheCongo": "Democratic Republic of the Congo",
    "CentralAfricanRepublic": "Central African Republic",
    "SierraLeone": "Sierra Leone", "ElSalvador": "El Salvador",
    "CostaRica": "Costa Rica", "DominicanRepublic": "Dominican Republic",
    "PapuaNewGuinea": "Papua New Guinea", "UnitedArabEmirates": "United Arab Emirates",
    "HongKong": "Hong Kong S.A.R.", "Palestina": "Palestine",
    "Burma": "Myanmar",
    "Serbia": "Republic of Serbia", "Tanzania": "United Republic of Tanzania",
    # Bahrain and Singapore are absent from the 110m basemap (too small to render)
}


def to_ne_name(name):
    if name in NAME_TO_NE:
        return NAME_TO_NE[name]
    # split concatenated CamelCase names ("SouthSudan" -> "South Sudan")
    import re
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def main():
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]

    cty = pd.read_csv(CTY_CSV)
    valid = (cty.exDmg_mean > 0) & (cty.exInunD_mean > 0)
    for metric, col in [("exDmg_mean", "tert_FD"), ("exInunD_mean", "tert_IR")]:
        cty[col] = np.nan
        cty.loc[valid, col] = pd.qcut(cty.loc[valid, metric], 3, labels=False)
    cty["ne_name"] = cty["country_na"].map(to_ne_name)

    d = (cty.tert_IR - cty.tert_FD)[valid]
    print(f"tertile shifts (n={valid.sum()}): lower={(d < 0).sum()} higher={(d > 0).sum()} same={(d == 0).sum()}")

    world = gpd.read_file(SHP)[["ADMIN", "geometry"]]
    world = world[world.ADMIN != "Antarctica"]
    merged = world.merge(cty[["ne_name", "tert_FD", "tert_IR"]],
                         left_on="ADMIN", right_on="ne_name", how="left")
    matched = set(merged.dropna(subset=["ne_name"]).ne_name)
    unmatched = sorted(set(cty.ne_name) - matched)
    if unmatched:
        print("[warn] not matched to basemap:", unmatched)
    merged = merged.to_crs("ESRI:54009")  # Mollweide

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 7.6))
    for ax, col, sub in [(axes[0], "tert_FD", "(a) FD-AED tertile ranking"),
                         (axes[1], "tert_IR", "(b) IR-AED tertile ranking")]:
        merged.plot(ax=ax, color=NODATA, edgecolor="white", linewidth=0.3)
        for t in (0, 1, 2):
            merged[merged[col] == t].plot(ax=ax, color=TERTILE_COLORS[t],
                                          edgecolor="white", linewidth=0.3)
        ax.set_title(sub, fontsize=10, loc="left", fontweight="bold")
        ax.set_axis_off()

    handles = [Patch(facecolor=c, edgecolor="0.6", linewidth=0.4, label=l)
               for c, l in zip(TERTILE_COLORS, LABELS)]
    handles.append(Patch(facecolor=NODATA, edgecolor="0.6", linewidth=0.4, label="No data"))
    fig.legend(handles=handles, ncol=4, loc="lower center",
               bbox_to_anchor=(0.5, 0.015), fontsize=8.5, frameon=False,
               columnspacing=1.2, handletextpad=0.5)

    fig.tight_layout(rect=(0, 0.04, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"Fig2_tertile_maps_2026-7.{ext}", dpi=300,
                    bbox_inches="tight", facecolor="white")
    print("saved", OUT_DIR / "Fig2_tertile_maps_2026-7.png")


if __name__ == "__main__":
    main()
