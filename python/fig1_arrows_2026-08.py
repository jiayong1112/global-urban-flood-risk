"""
Figure 1 as embedded in the manuscript (arrows variant), third revision.

The submitted manuscript carries the arrows variant of Figure 1, produced by
code/figures/fig1_variants_2026-7.py, not the plain dumbbell version. This
script reproduces that design exactly and applies the one change of this
revision: Russia moves from Central Asia to Europe (region_map.py).

Output: Fig1_arrows_2026-08.png / .pdf, at the same figure size and dpi as the
previously submitted image so it drops into the manuscript unchanged in shape.
"""

import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

from region_map import REGION_MAP, DISPLAY

import paths

HERE = Path(__file__).resolve().parent
REGION_CSV = paths.table("gdp_normalized_region_2026-08b.csv")

_spec = importlib.util.spec_from_file_location(
    "fig1_2026_08", HERE / "fig1_regional_metrics_2026-08.py")
fig1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fig1)

COL = fig1.COL
ORDER = ["Africa", "N America", "C America", "S America",
         "E Asia", "C Asia", "S Asia", "SE Asia", "SW Asia", "Europe", "Oceania"]
NOTE = "Arrows point from the damage before protection to the damage after protection."


def draw_arrow(ax, x_pre, x_post, y, color):
    ax.add_patch(FancyArrowPatch(
        (x_pre, y), (x_post, y), arrowstyle="-|>", mutation_scale=8.5,
        lw=1.3, color=color, alpha=0.6, shrinkA=3.5, shrinkB=3.5,
        joinstyle="miter", zorder=2))


def draw_panel(ax, data, title, xlabel, log=False):
    n = len(ORDER)
    off = 0.19
    ax.set_axisbelow(True)
    for i in range(0, n, 2):
        ax.axhspan(n - 1 - i - 0.5, n - 1 - i + 0.5,
                   facecolor="0.945", edgecolor="none", zorder=0)
    for i, rgn in enumerate(ORDER):
        y = n - 1 - i
        row = data.loc[rgn]
        for met, dy in (("FD", +off), ("IR", -off)):
            pre, post = row[met], row[f"{met}_P"]
            draw_arrow(ax, pre, post, y + dy, COL[met])
            ax.plot(pre, y + dy, "o", ms=5.2, color=COL[met],
                    mec="white", mew=0.7, zorder=3)
            ax.plot(post, y + dy, "o", ms=5.2, color=COL[f"{met}_P"],
                    mec="white", mew=0.7, zorder=3)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_yticks(range(n))
    ax.set_yticklabels([DISPLAY[r] for r in ORDER[::-1]])
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

    f = fig1.load_fua()
    a, n_fua, _ = fig1.panel_a(f, REGION_MAP)
    r = pd.read_csv(REGION_CSV, index_col=0)
    b = pd.DataFrame({"FD": r["exDmg_bnUSD"], "FD_P": r["exDmg_pros_bnUSD"],
                      "IR": r["exInunD_bnUSD"], "IR_P": r["exInunD_pros_bnUSD"]})
    c = pd.DataFrame({"FD": r["exDmg_pctGDP"], "FD_P": r["exDmg_pros_pctGDP"],
                      "IR": r["exInunD_pctGDP"], "IR_P": r["exInunD_pros_pctGDP"]})
    print(f"panel (a) built from {n_fua} FUAs")

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 4.6))
    draw_panel(axes[0], a, "(a) Share of global risk intensity",
               "% of global (FUA-mean metrics)")
    draw_panel(axes[1], b, "(b) GDP-weighted expected loss",
               "billion US$ per year (log scale)", log=True)
    draw_panel(axes[2], c, "(c) Loss relative to economy",
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
               bbox_to_anchor=(0.5, 0.035), fontsize=8, frameon=False,
               columnspacing=1.4, handletextpad=0.4)
    fig.text(0.5, 0.012, NOTE, ha="center", fontsize=7.5, color="0.30")

    fig.tight_layout(rect=(0, 0.10, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(paths.out(f"Fig1_arrows_2026-08.{ext}"), dpi=300,
                    bbox_inches="tight", facecolor="white")
    print("saved", paths.out("Fig1_arrows_2026-08.png"))


if __name__ == "__main__":
    main()
