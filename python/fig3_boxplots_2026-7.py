"""
Figure 3 (Jul 2026 revision): distribution of the four AED metrics at
(a) country and (b) FUA scale. Boxplots with jittered points.

Reviewer requests implemented: points are distinguished by COLOR (world region)
instead of symbols, with transparency to reduce overplotting.

Region palette: 11 colors selected by randomized search over Paul Tol color pools,
maximizing worst-pair separation under simulated protanopia/deuteranopia/tritanopia
(all but one pair dE >= 8 under CVD; worst pair 7.8).

Data: fua_world_countries_2026-1-8.csv (108 countries) and
csv_fua_2026-1-17/JRC_*_FloodRisk.csv (633 FUAs; Oceania means from sum/count).
"""

import pandas as pd
import numpy as np
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SUB = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission"
OUT_DIR = BASE / "figures"

_txt = (BASE / "code" / "figures" / "compute_gdp_normalized_2026-7.py").read_text()
_ns = {}
exec(re.search(r"REGION_MAP = \{.*?\n\}", _txt, re.S).group(0), _ns)
REGION_MAP = _ns["REGION_MAP"]

METS = ["exDmg_mean", "exDmg_pros_mean", "exInunD_mean", "exInunD_pros_mean"]
MET_LABELS = ["FD-AED", "FD-AED\nafter protection", "IR-AED", "IR-AED\nafter protection"]

REGION_ORDER = ["C America", "S America", "Oceania", "E Asia", "S Asia", "SE Asia",
                "N America", "SW Asia", "Europe", "C Asia", "Africa"]
REGION_COLORS = {
    "C America": "#AA4499", "S America": "#000000", "Oceania": "#99DDFF",
    "E Asia": "#EE3377", "S Asia": "#882255", "SE Asia": "#EE7733",
    "N America": "#6699CC", "SW Asia": "#FFAABB", "Europe": "#004488",
    "C Asia": "#BBCC33", "Africa": "#117733",
}
DISPLAY = {
    "C America": "Central America", "S America": "South America", "N America": "North America",
    "E Asia": "East Asia", "SE Asia": "Southeast Asia", "S Asia": "South Asia",
    "SW Asia": "Southwest Asia", "C Asia": "Central Asia",
    "Europe": "Europe", "Africa": "Africa", "Oceania": "Oceania",
}


def load_country():
    cty = pd.read_csv(SUB / "fua_world_countries_2026-1-8.csv")
    return cty.dropna(subset=["wld_rgn"])


def load_fua():
    frames = []
    for c in ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]:
        df = pd.read_csv(SUB / "csv_fua_2026-1-17" / f"JRC_{c}_FloodRisk.csv")
        for m in METS:
            if m not in df.columns:
                base = m.replace("_mean", "")
                df[m] = df[f"{base}_sum"] / df[f"{base}_count"]
        frames.append(df)
    f = pd.concat(frames, ignore_index=True).drop_duplicates("eFUA_ID", keep="first")
    f["wld_rgn"] = f["Cntry_name"].map(REGION_MAP)
    return f.dropna(subset=["wld_rgn"])


def draw_panel(ax, df, title, point_size, point_alpha, rng):
    data = [100 * df[m].dropna() for m in METS]
    bp = ax.boxplot(data, positions=range(4), widths=0.55, showfliers=False,
                    patch_artist=True, zorder=4,
                    boxprops=dict(facecolor="none", edgecolor="0.25", lw=1.0),
                    whiskerprops=dict(color="0.25", lw=1.0),
                    capprops=dict(color="0.25", lw=1.0),
                    medianprops=dict(color="0.1", lw=1.4))
    for i, m in enumerate(METS):
        sub = df.dropna(subset=[m])
        x = i + rng.uniform(-0.22, 0.22, len(sub))
        colors = sub["wld_rgn"].map(REGION_COLORS)
        ax.scatter(x, 100 * sub[m], s=point_size, c=colors, alpha=point_alpha,
                   linewidths=0, zorder=2)
    ax.set_xticks(range(4))
    ax.set_xticklabels(MET_LABELS, fontsize=7.5)
    ax.set_ylabel("Annual expected damage (%)", fontsize=8)
    ax.set_title(title, fontsize=9, loc="left", fontweight="bold")
    ax.grid(axis="y", color="0.9", lw=0.6, zorder=0)
    ax.tick_params(labelsize=8, length=2.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_ylim(0, 10)


def main():
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    rng = np.random.default_rng(20260720)

    cty, fua = load_country(), load_fua()
    print(f"countries: {len(cty)}, FUAs: {len(fua)}")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.3), sharey=True)
    draw_panel(axes[0], cty, f"(a) Country level (n = {len(cty)})", 14, 0.65, rng)
    draw_panel(axes[1], fua, f"(b) Urban level (n = {len(fua)} FUAs)", 7, 0.4, rng)
    axes[1].set_ylabel("")

    handles = [Line2D([], [], marker="o", ls="", ms=5, color=REGION_COLORS[r],
                      alpha=0.85, label=DISPLAY[r]) for r in REGION_ORDER]
    fig.legend(handles=handles, ncol=4, loc="lower center",
               bbox_to_anchor=(0.5, -0.01), fontsize=7.5, frameon=False,
               columnspacing=1.0, handletextpad=0.3)

    fig.tight_layout(rect=(0, 0.10, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"Fig3_boxplots_2026-7.{ext}", dpi=300,
                    bbox_inches="tight", facecolor="white")
    print("saved", OUT_DIR / "Fig3_boxplots_2026-7.png")


if __name__ == "__main__":
    main()
