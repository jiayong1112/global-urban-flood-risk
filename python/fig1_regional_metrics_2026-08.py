"""
Figure 1, third revision (August 2026).

Identical in design and method to code/figures/fig1_regional_metrics_2026-7.py.
The only change is the region mapping, which now places Russia in Europe
(region_map.py), matching Table S2 of the manuscript.

Panel (a) aggregates FUA -> country mean -> region mean, as before.
Panels (b, c) read gdp_normalized_region_2026-08b.csv.

All four indicators come from the 2026-08 export (a5_fua_2026-08.csv and
gdp_normalized_region_2026-08b.csv), so panels (a), (b) and (c) share one source.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from pathlib import Path

from region_map import REGION_MAP, PUBLISHED_REGION_MAP, DISPLAY

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
SRC = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission" / "csv_fua_2026-1-17"
PUBLISHED_PANEL_A = BASE / "data" / "fig1_panelA_shares_2026-7.csv"

METS = ["exDmg_mean", "exInunD_mean", "exDmg_pros_mean", "exInunD_pros_mean"]
COL = {"FD": "#0072B2", "FD_P": "#56B4E9", "IR": "#D55E00", "IR_P": "#E69F00"}


def load_fua():
    """The 2026-08 export: symmetric rare-event tail, FLOPROS masking, and the
    9 FUAs the January export had dropped (Mexico City among them)."""
    return pd.read_csv(BASE / "revision-2026-08" / "analysis" / "a5_fua_2026-08.csv")


def panel_a(f, mapping):
    d = f.copy()
    d["wld_rgn"] = d["Cntry_name"].map(mapping)
    d = d.dropna(subset=["wld_rgn"])
    cty = d.groupby(["Cntry_name", "wld_rgn"])[METS].mean().reset_index()
    reg = cty.groupby("wld_rgn")[METS].mean()
    shares = 100 * reg / reg.sum()
    shares.columns = ["FD", "IR", "FD_P", "IR_P"]
    return shares, len(d), cty["wld_rgn"].value_counts()


def draw_panel(ax, data, order, title, xlabel, log=False):
    n = len(order)
    off = 0.19
    ax.set_axisbelow(True)
    for i in range(0, n, 2):
        ax.axhspan(n - 1 - i - 0.5, n - 1 - i + 0.5,
                   facecolor="0.945", edgecolor="none", zorder=0)
    for i, rgn in enumerate(order):
        y = n - 1 - i
        row = data.loc[rgn]
        for met, dy in (("FD", +off), ("IR", -off)):
            pre, post = row[met], row[f"{met}_P"]
            ax.plot([post, pre], [y + dy, y + dy], color=COL[met], lw=1.4,
                    alpha=0.45, solid_capstyle="round", zorder=2)
            ax.plot(pre, y + dy, "o", ms=5.2, color=COL[met],
                    mec="white", mew=0.7, zorder=3)
            ax.plot(post, y + dy, "o", ms=5.2, color=COL[f"{met}_P"],
                    mec="white", mew=0.7, zorder=3)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_yticks(range(n))
    ax.set_yticklabels([DISPLAY[r] for r in order[::-1]])
    if log:
        ax.set_xscale("log")
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_title(title, fontsize=9, loc="left", fontweight="bold", pad=8)
    ax.grid(axis="x", color="0.88", lw=0.6, zorder=0)
    ax.tick_params(axis="both", labelsize=8, length=2.5)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("0.55")


def main():
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    f = load_fua()

    a, n_new, cty_counts = panel_a(f, REGION_MAP)
    a.round(4).to_csv(HERE / "fig1_panelA_shares_2026-08.csv")
    print(f"\ncorrected panel (a)  (n = {n_new} FUAs)")
    print(a.round(2).to_string())
    print("\ncountries per region:")
    print(cty_counts.to_string())

    g1 = ["Europe", "N America", "Oceania", "E Asia"]
    g2 = ["S Asia", "Africa", "C America"]
    for nm, grp in (("Europe+N America+Oceania+E Asia", g1), ("S Asia+Africa+C America", g2)):
        print(f"  {nm}: FD {a.loc[grp,'FD'].sum():.1f}% -> {a.loc[grp,'FD_P'].sum():.1f}%   "
              f"IR {a.loc[grp,'IR'].sum():.1f}% -> {a.loc[grp,'IR_P'].sum():.1f}%")
    for r in a.index:
        print(f"  {r:10s} FD {a.FD[r]:5.2f} -> IR {a.IR[r]:5.2f}  "
              f"({(a.IR[r]-a.FD[r])/a.FD[r]*100:+.0f}% relative; "
              f"depth-only is {(a.FD[r]-a.IR[r])/a.IR[r]*100:+.0f}% of IR)")

    r = pd.read_csv(HERE / "gdp_normalized_region_2026-08b.csv", index_col=0)
    b = pd.DataFrame({"FD": r["exDmg_bnUSD"], "FD_P": r["exDmg_pros_bnUSD"],
                      "IR": r["exInunD_bnUSD"], "IR_P": r["exInunD_pros_bnUSD"]})
    c = pd.DataFrame({"FD": r["exDmg_pctGDP"], "FD_P": r["exDmg_pros_pctGDP"],
                      "IR": r["exInunD_pctGDP"], "IR_P": r["exInunD_pros_pctGDP"]})

    order = ["Africa", "N America", "C America", "S America",
             "E Asia", "C Asia", "S Asia", "SE Asia", "SW Asia", "Europe", "Oceania"]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 4.4), sharey=False)
    draw_panel(axes[0], a, order, "(a) Share of global risk intensity",
               "% of global (FUA-mean metrics)")
    draw_panel(axes[1], b, order, "(b) GDP-weighted expected loss",
               "billion US$ per year (log scale)", log=True)
    draw_panel(axes[2], c, order, "(c) Loss relative to economy",
               "% of regional urban GDP per year")
    for ax in axes[1:]:
        ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)

    legend_items = [
        Line2D([], [], marker="o", ls="", ms=5.2, color=COL["FD"], mec="white", mew=0.7, label="FD-AED"),
        Line2D([], [], marker="o", ls="", ms=5.2, color=COL["FD_P"], mec="white", mew=0.7, label="FD-AED after protection"),
        Line2D([], [], marker="o", ls="", ms=5.2, color=COL["IR"], mec="white", mew=0.7, label="IR-AED"),
        Line2D([], [], marker="o", ls="", ms=5.2, color=COL["IR_P"], mec="white", mew=0.7, label="IR-AED after protection"),
    ]
    fig.legend(handles=legend_items, ncol=4, loc="lower center",
               bbox_to_anchor=(0.5, -0.005), fontsize=8, frameon=False,
               columnspacing=1.4, handletextpad=0.4)

    fig.tight_layout(rect=(0, 0.05, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"Fig1_regional_metrics_2026-08.{ext}", dpi=300,
                    bbox_inches="tight", facecolor="white")
    print("\nsaved", HERE / "Fig1_regional_metrics_2026-08.png")


if __name__ == "__main__":
    main()
