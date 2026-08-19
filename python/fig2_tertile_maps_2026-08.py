"""
Figure 2, third revision (August 2026).

Identical in design and method to code/figures/fig2_tertile_maps_2026-7.py.
The change is the input table: country_table_2026-08.csv now covers 126
countries instead of 108, because 18 countries that have functional urban areas
in the analysis and are listed in Table S2 had been missing from the region map.

Also prints the tertile-movement statistics reported in Results section 2.
"""

import re
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
SHP = BASE / "data" / "ne_110m_admin_0_countries" / "ne_110m_admin_0_countries.shp"

TERTILE_COLORS = ["#ffeda0", "#feb24c", "#f03b20"]
NODATA = "#d9d9d9"
LABELS = ["Low (bottom third)", "Medium (middle third)", "High (top third)"]

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
}


def to_ne_name(name):
    if name in NAME_TO_NE:
        return NAME_TO_NE[name]
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def main():
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]

    cty = pd.read_csv(BASE / "revision-2026-08" / "analysis" / "a5_country_2026-08.csv")
    valid = (cty.exDmg_mean > 0) & (cty.exInunD_mean > 0)
    for metric, col in [("exDmg_mean", "tert_FD"), ("exInunD_mean", "tert_IR")]:
        cty[col] = np.nan
        cty.loc[valid, col] = pd.qcut(cty.loc[valid, metric], 3, labels=False)
    cty["ne_name"] = cty["country_na"].map(to_ne_name)

    v = cty[valid].copy()
    v["shift"] = v.tert_IR - v.tert_FD
    print(f"countries with valid values: {len(v)} of {len(cty)}")
    lower, higher, same = (v["shift"] < 0), (v["shift"] > 0), (v["shift"] == 0)
    print(f"  to a LOWER tertile : {lower.sum():3d}  mean height {v.loc[lower,'height_mean'].mean():.1f} m")
    print(f"  to a HIGHER tertile: {higher.sum():3d}  mean height {v.loc[higher,'height_mean'].mean():.1f} m")
    print(f"  unchanged          : {same.sum():3d}")
    two = v[v["shift"].abs() == 2]
    print(f"  two-tertile jumps  : "
          + (", ".join(f"{r.country_na} ({int(r.tert_FD)}->{int(r.tert_IR)})"
                       for r in two.itertuples()) or "none"))

    print("\n  worsening, by region:")
    for rg, grp in v[higher].groupby("wld_rgn"):
        print(f"    {rg:10s} " + ", ".join(
            f"{r.country_na} ({r.height_mean:.1f} m)"
            for r in grp.sort_values("height_mean").itertuples()))
    print("\n  improving, by region:")
    for rg, grp in v[lower].groupby("wld_rgn"):
        print(f"    {rg:10s} " + ", ".join(
            f"{r.country_na} ({r.height_mean:.1f} m)"
            for r in grp.sort_values("height_mean").itertuples()))

    hi = v[(v.tert_FD == 2) & (v.tert_IR == 2)].copy()
    hi["red"] = 1 - hi.exDmg_pros_mean / hi.exDmg_mean
    print(f"\n  remain HIGH under both metrics: {len(hi)}")
    print("    " + ", ".join(sorted(hi.country_na)))
    print("    best protection:  " + ", ".join(
        f"{r.country_na} ({r.red*100:.0f}%)" for r in hi.nlargest(6, "red").itertuples()))
    print("    least protection: " + ", ".join(
        f"{r.country_na} ({r.red*100:.0f}%)" for r in hi.nsmallest(6, "red").itertuples()))

    world = gpd.read_file(SHP)[["ADMIN", "geometry"]]
    world = world[world.ADMIN != "Antarctica"]
    merged = world.merge(cty[["ne_name", "tert_FD", "tert_IR"]],
                         left_on="ADMIN", right_on="ne_name", how="left")
    unmatched = sorted(set(cty.ne_name) - set(merged.dropna(subset=["ne_name"]).ne_name))
    if unmatched:
        print("\n[warn] not matched to basemap:", unmatched)
    merged = merged.to_crs("ESRI:54009")

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
        fig.savefig(HERE / f"Fig2_tertile_maps_2026-08.{ext}", dpi=300,
                    bbox_inches="tight", facecolor="white")
    print("\nsaved", HERE / "Fig2_tertile_maps_2026-08.png")


if __name__ == "__main__":
    main()
