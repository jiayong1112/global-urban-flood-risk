"""
Figure 1 (Jul 2026 revision): regional flood risk across three economic perspectives.

Replaces the Sankey + world map design. Three aligned panels, one row per world
region, two protection dumbbells per row (FD-AED and IR-AED, pre -> post protection):
  (a) share of global risk intensity (normalized FUA-mean metrics, % of global)
  (b) GDP-weighted expected annual loss (billion USD, log scale)
  (c) expected annual loss as % of regional urban GDP  [NEW - reviewer request]

Panel (a) reproduces the submitted manuscript numbers exactly (FUA -> country mean
-> region mean over the csv_fua_2026-1-17 JRC data; Oceania means from sum/count).
Panels (b, c) read data/gdp_normalized_region_2026-7.csv (compute_gdp_normalized_2026-7.py).

Colors (Okabe-Ito, CVD-validated: all pairs dE >= 8 under protan/deutan/tritan simulation):
  FD-AED #0072B2, FD-AED-P #56B4E9, IR-AED #D55E00, IR-AED-P #E69F00
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
SRC_1_17 = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission" / "csv_fua_2026-1-17"
REGION_CSV = BASE / "data" / "gdp_normalized_region_2026-7.csv"
OUT_DIR = BASE / "figures"

# reuse the region mapping from the normalization script
_txt = (BASE / "code" / "figures" / "compute_gdp_normalized_2026-7.py").read_text()
_ns = {}
exec(re.search(r"REGION_MAP = \{.*?\n\}", _txt, re.S).group(0), _ns)
REGION_MAP = _ns["REGION_MAP"]

METS = ["exDmg_mean", "exInunD_mean", "exDmg_pros_mean", "exInunD_pros_mean"]
COL = {"FD": "#0072B2", "FD_P": "#56B4E9", "IR": "#D55E00", "IR_P": "#E69F00"}
DISPLAY = {
    "C America": "Central America", "S America": "South America", "N America": "North America",
    "E Asia": "East Asia", "SE Asia": "Southeast Asia", "S Asia": "South Asia",
    "SW Asia": "Southwest Asia", "C Asia": "Central Asia",
    "Europe": "Europe", "Africa": "Africa", "Oceania": "Oceania",
}


def panel_a_shares():
    frames = []
    for c in ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]:
        df = pd.read_csv(SRC_1_17 / f"JRC_{c}_FloodRisk.csv")
        for m in METS:
            if m not in df.columns:
                base = m.replace("_mean", "")
                df[m] = df[f"{base}_sum"] / df[f"{base}_count"]
        frames.append(df)
    f = pd.concat(frames, ignore_index=True).drop_duplicates("eFUA_ID", keep="first")
    f["wld_rgn"] = f["Cntry_name"].map(REGION_MAP)
    f = f.dropna(subset=["wld_rgn"])
    cty = f.groupby(["Cntry_name", "wld_rgn"])[METS].mean().reset_index()
    reg = cty.groupby("wld_rgn")[METS].mean()
    shares = 100 * reg / reg.sum()
    shares.columns = ["FD", "IR", "FD_P", "IR_P"]
    return shares


def draw_panel(ax, data, order, title, xlabel, log=False):
    n = len(order)
    off = 0.19
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

    a = panel_a_shares()
    a.round(4).to_csv(BASE / "data" / "fig1_panelA_shares_2026-7.csv")

    r = pd.read_csv(REGION_CSV, index_col=0)
    b = pd.DataFrame({
        "FD": r["exDmg_bnUSD"], "FD_P": r["exDmg_pros_bnUSD"],
        "IR": r["exInunD_bnUSD"], "IR_P": r["exInunD_pros_bnUSD"]})
    c = pd.DataFrame({
        "FD": r["exDmg_pctGDP"], "FD_P": r["exDmg_pros_pctGDP"],
        "IR": r["exInunD_pctGDP"], "IR_P": r["exInunD_pros_pctGDP"]})

    # fixed alphabetical grouping (top to bottom): Africa; Americas; Asias; Europe; Oceania
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
    OUT_DIR.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"Fig1_regional_metrics_2026-7.{ext}", dpi=300,
                    bbox_inches="tight", facecolor="white")
    print("saved", OUT_DIR / "Fig1_regional_metrics_2026-7.png")


if __name__ == "__main__":
    main()
