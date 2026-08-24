"""
Figure 3, third revision (August 2026).

Identical in design and method to code/figures/fig3_boxplots_2026-7.py. The only
change is the region mapping used to color the points, which now places Russia
in Europe (region_map.py) instead of Central Asia. Panel (a) previously
took its region labels from the wld_rgn column of fua_world_countries_2026-1-8.csv;
it now maps Cntry_name through the same corrected mapping as panel (b), so the two
panels cannot disagree.

The plotted values are unchanged: only the colors of Russia's 1 country point and
15 FUA points, and the legend grouping, differ from the previously submitted figure.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from pathlib import Path

from region_map import REGION_MAP, PUBLISHED_REGION_MAP, DISPLAY

import paths

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


def load_country():
    """Extended country table (126 countries), built by country_table_2026-08.py."""
    cty = pd.read_csv(paths.table("a5_country_2026-08.csv"))
    print(f"  country table: {len(cty)} countries (2026-08 export)")
    return cty.dropna(subset=["wld_rgn"])


def load_fua():
    f = pd.read_csv(paths.table("a5_fua_2026-08.csv"))
    return f.dropna(subset=["wld_rgn"])


def draw_panel(ax, df, title, point_size, point_alpha, rng):
    data = [100 * df[m].dropna() for m in METS]
    ax.boxplot(data, positions=range(4), widths=0.55, showfliers=False,
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


def report(df, label):
    iqr = lambda s: s.quantile(.75) - s.quantile(.25)
    print(f"\n  {label} (n = {len(df)})")
    for m in METS:
        s = df[m].dropna()
        print(f"    {m:18s} median {100*s.median():5.2f}%  IQR {100*iqr(s):4.2f} pp"
              f"  CV {s.std()/s.mean()*100:5.1f}%")
    for pre, post, nm in ((METS[0], METS[1], "FD-AED"), (METS[2], METS[3], "IR-AED")):
        red = (1 - df[post] / df[pre]).replace([np.inf, -np.inf], np.nan).dropna()
        print(f"    {nm}: mean protection reduction {red.mean()*100:.1f}%,"
              f" IQR compression {(1 - iqr(df[post].dropna())/iqr(df[pre].dropna()))*100:.0f}%")


def main():
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    rng = np.random.default_rng(20260720)

    cty, fua = load_country(), load_fua()
    print(f"countries: {len(cty)}, FUAs: {len(fua)}")
    report(cty, "country level")
    report(fua, "urban level")

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
        fig.savefig(paths.out(f"Fig3_boxplots_2026-08.{ext}"), dpi=300,
                    bbox_inches="tight", facecolor="white")
    print("\nsaved", paths.out("Fig3_boxplots_2026-08.png"))


if __name__ == "__main__":
    main()
