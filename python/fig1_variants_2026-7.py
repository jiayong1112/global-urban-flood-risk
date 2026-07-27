"""
Figure 1 design alternatives (Jul 2026 revision): emphasize the CHANGE from
damage before protection to damage after protection.

Variant A (arrows):       connectors drawn as arrows pointing before -> after
Variant B (dash-to-solid): connectors run from dashed (before) to solid (after)

Data, region order, and colors are reused from fig1_regional_metrics_2026-7.py,
so all plotted values are identical to the current Figure 1.

Outputs (figures/):
  Fig1_alt_arrows_2026-7.png / .pdf
  Fig1_alt_dash2solid_2026-7.png / .pdf
"""

import importlib.util
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OUT_DIR = BASE / "figures"
REGION_CSV = BASE / "data" / "gdp_normalized_region_2026-7.csv"

# reuse the existing Figure 1 module (hyphenated filename -> load by path)
_spec = importlib.util.spec_from_file_location(
    "fig1_base", Path(__file__).with_name("fig1_regional_metrics_2026-7.py"))
fig1_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fig1_base)

COL = fig1_base.COL
DISPLAY = fig1_base.DISPLAY

ORDER = ["Africa", "N America", "C America", "S America",
         "E Asia", "C Asia", "S Asia", "SE Asia", "SW Asia", "Europe", "Oceania"]

# dash pattern progression: sparse dashes (before) -> solid (after)
DASH_STEPS = [(0, (0.9, 2.6)), (0, (1.3, 2.2)), (0, (1.9, 1.9)),
              (0, (2.6, 1.6)), (0, (3.6, 1.3)), (0, (5.0, 1.0)), "solid"]


def _interp(x0, x1, t, log):
    if log:
        return 10 ** (np.log10(x0) + t * (np.log10(x1) - np.log10(x0)))
    return x0 + t * (x1 - x0)


def draw_flow(ax, x_pre, x_post, y, color, log):
    """Dashed at the 'before' end, progressively solid toward the 'after' end."""
    n = len(DASH_STEPS)
    for i, dash in enumerate(DASH_STEPS):
        a = _interp(x_pre, x_post, i / n, log)
        b = _interp(x_pre, x_post, (i + 1) / n, log)
        ax.plot([a, b], [y, y], color=color, solid_capstyle="butt",
                lw=1.0 + 0.7 * (i / (n - 1)), alpha=0.35 + 0.5 * (i / (n - 1)),
                ls=dash, zorder=2)


def draw_arrow(ax, x_pre, x_post, y, color):
    """Arrow pointing from the 'before' value to the 'after' value."""
    ax.add_patch(FancyArrowPatch(
        (x_pre, y), (x_post, y), arrowstyle="-|>", mutation_scale=8.5,
        lw=1.3, color=color, alpha=0.6, shrinkA=3.5, shrinkB=3.5,
        joinstyle="miter", zorder=2))


def draw_panel(ax, data, title, xlabel, style, log=False):
    n = len(ORDER)
    off = 0.19
    for i, rgn in enumerate(ORDER):
        y = n - 1 - i
        row = data.loc[rgn]
        for met, dy in (("FD", +off), ("IR", -off)):
            pre, post = row[met], row[f"{met}_P"]   # before, after protection
            if style == "arrows":
                draw_arrow(ax, pre, post, y + dy, COL[met])
            else:
                draw_flow(ax, pre, post, y + dy, COL[met], log)
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


def build(style, outname, note):
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]

    a = fig1_base.panel_a_shares()
    r = pd.read_csv(REGION_CSV, index_col=0)
    b = pd.DataFrame({"FD": r["exDmg_bnUSD"], "FD_P": r["exDmg_pros_bnUSD"],
                      "IR": r["exInunD_bnUSD"], "IR_P": r["exInunD_pros_bnUSD"]})
    c = pd.DataFrame({"FD": r["exDmg_pctGDP"], "FD_P": r["exDmg_pros_pctGDP"],
                      "IR": r["exInunD_pctGDP"], "IR_P": r["exInunD_pros_pctGDP"]})

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 4.6))
    draw_panel(axes[0], a, "(a) Share of global risk intensity",
               "% of global (FUA-mean metrics)", style)
    draw_panel(axes[1], b, "(b) GDP-weighted expected loss",
               "billion US$ per year (log scale)", style, log=True)
    draw_panel(axes[2], c, "(c) Loss relative to economy",
               "% of regional urban GDP per year", style)
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
    fig.text(0.5, 0.012, note, ha="center", fontsize=7.5, color="0.30")

    fig.tight_layout(rect=(0, 0.10, 1, 1))
    OUT_DIR.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"{outname}.{ext}", dpi=300,
                    bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", OUT_DIR / f"{outname}.png")


if __name__ == "__main__":
    build("arrows", "Fig1_alt_arrows_2026-7",
          "Arrows point from the damage before protection to the damage after protection.")
    build("dash2solid", "Fig1_alt_dash2solid_2026-7",
          "Connectors run from dashed (before protection) to solid (after protection).")
