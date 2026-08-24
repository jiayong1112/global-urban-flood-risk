"""
A2 - Worked decision-support numbers (Reviewer 3, Comment 4).

Reviewer 3 asks how the improved AED estimates could support flood mitigation
planning, investment prioritisation, and cost-benefit analysis. The manuscript
already contrasts Wuhan (100-yr standard) with Bangkok (~28-yr standard) in the
Results; this script turns that contrast into the annual benefit stream that
would enter an appraisal.

What is computed
----------------
For a set of illustrative FUAs:
  * FD-AED and IR-AED, before and after protection (fraction of exposed value)
  * GDP-weighted expected annual loss, before and after protection (USD/yr)
  * Avoided annual loss = unprotected minus residual (USD/yr), i.e. the annual
    benefit attributable to the modelled protection standard
  * The same, expressed as a share of the FUA's total urban GDP

Important framing for the manuscript: this is the *benefit* side only. We hold
no construction or maintenance cost data, so this is an illustration of how the
metrics feed an appraisal, not a costed appraisal.

Run:  python a2_decision_support_numbers.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

import paths

SRC = paths.FUA_2026_01
GDP_TOTAL = paths.TOTAL_GDP_CSV
OUT = paths.OUTPUT

CITIES = ["Wuhan", "Bangkok", "Shanghai", "Dhaka", "Ho Chi Minh City",
          "Mandalay", "Hanoi", "Phnom Penh"]


def main() -> None:
    risk = pd.read_csv(SRC / "JRC_Asia_FloodRisk.csv")
    gdp = pd.read_csv(SRC / "JRC_Asia_GDP.csv")
    tot = pd.read_csv(GDP_TOTAL).rename(columns={"sum": "totalGDP_usd"})

    df = risk[["eFUA_ID", "eFUA_name", "Cntry_name", "height_mean",
               "flopros_merge_mean", "flopros_model_mean",
               "exDmg_mean", "exDmg_pros_mean",
               "exInunD_mean", "exInunD_pros_mean"]].copy()

    df = df.merge(
        gdp[["eFUA_ID", "exDmg_sum", "exDmg_pros_sum",
             "exInunD_sum", "exInunD_pros_sum"]],
        on="eFUA_ID", how="left")
    df = df.merge(tot[["eFUA_ID", "totalGDP_usd"]], on="eFUA_ID", how="left")

    # Annual benefit attributable to the modelled protection standard.
    df["avoided_fd_usd"] = df["exDmg_sum"] - df["exDmg_pros_sum"]
    df["avoided_ir_usd"] = df["exInunD_sum"] - df["exInunD_pros_sum"]

    for col, new in (("exDmg_sum", "fd_pctGDP"),
                     ("exDmg_pros_sum", "fd_pros_pctGDP"),
                     ("exInunD_sum", "ir_pctGDP"),
                     ("exInunD_pros_sum", "ir_pros_pctGDP"),
                     ("avoided_fd_usd", "avoided_fd_pctGDP"),
                     ("avoided_ir_usd", "avoided_ir_pctGDP")):
        df[new] = df[col] / df["totalGDP_usd"] * 100

    df["fd_reduction_pct"] = (1 - df["exDmg_pros_mean"] / df["exDmg_mean"]) * 100
    df["ir_reduction_pct"] = (1 - df["exInunD_pros_mean"] / df["exInunD_mean"]) * 100

    sel = df[df["eFUA_name"].isin(CITIES)].copy()
    # Where a city name maps to several FUAs, keep the one with most GDP.
    sel = sel.sort_values("totalGDP_usd", ascending=False)
    sel = sel.drop_duplicates(subset="eFUA_name", keep="first")
    sel = sel.set_index("eFUA_name").reindex(
        [c for c in CITIES if c in set(sel["eFUA_name"] if "eFUA_name" in sel
                                       else sel.index)]).reset_index()

    pd.set_option("display.width", 200)
    print("=" * 100)
    print("A2  Decision-support illustration - benefit side of a CBA")
    print("=" * 100)

    for _, r in sel.iterrows():
        print(f"\n{r['eFUA_name']} ({r['Cntry_name']})")
        print(f"  mean building height          : {r['height_mean']:.2f} m")
        print(f"  FLOPROS standard (merge layer): {r['flopros_merge_mean']:.1f} yr"
              f"   (model layer {r['flopros_model_mean']:.1f} yr)")
        print(f"  total urban GDP               : ${r['totalGDP_usd']/1e9:,.1f} B")
        print(f"  FD-AED   {r['exDmg_mean']*100:5.2f}% -> {r['exDmg_pros_mean']*100:5.2f}%"
              f"  after protection  ({r['fd_reduction_pct']:.0f}% reduction)")
        print(f"  IR-AED   {r['exInunD_mean']*100:5.2f}% -> {r['exInunD_pros_mean']*100:5.2f}%"
              f"  after protection  ({r['ir_reduction_pct']:.0f}% reduction)")
        print(f"  expected annual loss (FD, GDP-weighted): "
              f"${r['exDmg_sum']/1e9:6.2f} B/yr -> ${r['exDmg_pros_sum']/1e9:6.2f} B/yr")
        print(f"  avoided annual loss (FD)      : ${r['avoided_fd_usd']/1e9:6.2f} B/yr"
              f"  = {r['avoided_fd_pctGDP']:.3f}% of urban GDP")
        print(f"  avoided annual loss (IR)      : ${r['avoided_ir_usd']/1e9:6.2f} B/yr"
              f"  = {r['avoided_ir_pctGDP']:.3f}% of urban GDP")

    cols = ["eFUA_name", "Cntry_name", "height_mean", "flopros_merge_mean",
            "totalGDP_usd", "exDmg_mean", "exDmg_pros_mean", "exInunD_mean",
            "exInunD_pros_mean", "exDmg_sum", "exDmg_pros_sum", "avoided_fd_usd",
            "avoided_fd_pctGDP", "exInunD_sum", "exInunD_pros_sum",
            "avoided_ir_usd", "avoided_ir_pctGDP"]
    sel[cols].to_csv(paths.out("a2_decision_support_2026-08.csv"), index=False)

    # Global context: how large is the total modelled protection benefit?
    print("\n" + "-" * 100)
    print("Asia-wide context (all FUAs in the JRC Asia export with GDP data)")
    print("-" * 100)
    ok = df.dropna(subset=["exDmg_sum", "exDmg_pros_sum"])
    print(f"  n FUAs = {len(ok)}")
    print(f"  expected annual loss before protection: ${ok['exDmg_sum'].sum()/1e9:,.1f} B/yr")
    print(f"  expected annual loss after protection : ${ok['exDmg_pros_sum'].sum()/1e9:,.1f} B/yr")
    print(f"  avoided annual loss                   : "
          f"${ok['avoided_fd_usd'].sum()/1e9:,.1f} B/yr")

    print("\nWrote a2_decision_support.csv")


if __name__ == "__main__":
    main()
