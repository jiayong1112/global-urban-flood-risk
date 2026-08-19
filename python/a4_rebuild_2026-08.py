"""
A4 - Rebuild the FUA and country tables on the corrected run, and recompute
every quantity the manuscript reports.

Corrected run (revision-2026-08):
  * the rare-event tail term D(d500) x 0.002 is applied to the protected AND
    the unprotected metrics, so both are integrated over the same probability
    range (previously it was applied only to the protected metrics);
  * FD-AED and IR-AED are both averaged over the common built-up floodplain,
    so the comparison between them is like-for-like (previously FD-AED was
    averaged over the whole modelled floodplain and IR-AED over the built-up
    subset of it).

Column mapping from a3_diag_JRC.csv:
  exDmg_tail_mean   -> FD-AED     exDmg_pros_mean   -> FD-AED-P
  exInunD_tail_mean -> IR-AED     exInunD_pros_mean -> IR-AED-P
(the protected columns already carry the tail term)

Outputs
  a4_fua_2026-08.csv          per-FUA, corrected
  a4_country_2026-08.csv      per-country (mean over FUAs), corrected
  a4_fig1_panelA_2026-08.csv  regional shares for Figure 1a
Run:  python a4_rebuild_2026-08.py
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
SUB = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission"

# Region mapping reused verbatim from the published figure code, so regions
# match the previously published figures.
_txt = (BASE / "code" / "figures" / "compute_gdp_normalized_2026-7.py").read_text(encoding="utf-8")
_ns = {}
exec(re.search(r"REGION_MAP = \{.*?\n\}", _txt, re.S).group(0), _ns)
REGION_MAP = _ns["REGION_MAP"]

FD, IR, FDP, IRP = "FD_AED", "IR_AED", "FD_AED_P", "IR_AED_P"
RENAME = {"exDmg_tail_mean": FD, "exInunD_tail_mean": IR,
          "exDmg_pros_mean": FDP, "exInunD_pros_mean": IRP}
METS = [FD, FDP, IR, IRP]


def build():
    d = pd.read_csv(HERE / "a3_diag_JRC.csv").rename(columns=RENAME)
    d["wld_rgn"] = d["Cntry_name"].map(REGION_MAP)
    unmapped = sorted(d.loc[d.wld_rgn.isna(), "Cntry_name"].dropna().unique())
    if unmapped:
        print(f"  dropped (not in the published region map): {', '.join(unmapped)}")
    d = d.dropna(subset=METS + ["wld_rgn"])
    d = d[d[FD] > 0].copy()
    keep = ["eFUA_ID", "eFUA_name", "Cntry_name", "wld_rgn", "height_mean",
            "FUA_p_2015"] + METS + ["exDmgFP_mean", "exDmg_mean", "exInunD_mean",
                                    "exDmg_prosDn_mean", "exInunD_prosDn_mean"]
    d = d[[c for c in keep if c in d.columns]]

    cty = d.groupby(["Cntry_name", "wld_rgn"], as_index=False)[
        METS + ["height_mean"]].mean()
    cty["n_fuas"] = d.groupby(["Cntry_name", "wld_rgn"]).size().values
    return d, cty


def pct(x):
    return x * 100


def main():
    print("=" * 74)
    print("A4  Rebuild on the corrected run")
    print("=" * 74)
    fua, cty = build()
    print(f"  {len(fua)} FUAs, {len(cty)} countries, {fua.wld_rgn.nunique()} regions")

    fua.to_csv(HERE / "a4_fua_2026-08.csv", index=False)
    cty.to_csv(HERE / "a4_country_2026-08.csv", index=False)

    # ---- Figure 1a: FUA -> country mean -> region mean, share of global -----
    reg = cty.groupby("wld_rgn")[METS].mean()
    sh = 100 * reg / reg.sum()
    sh.to_csv(HERE / "a4_fig1_panelA_2026-08.csv")
    print("\n" + "-" * 74)
    print("Figure 1a - share of global total (%)")
    print("-" * 74)
    t = sh.copy()
    t["IR_vs_FD_%"] = (sh[IR] - sh[FD]) / sh[FD] * 100
    print(t.round(2).to_string())

    g1 = ["Europe", "N America", "Oceania", "E Asia"]
    g2 = ["S Asia", "Africa", "C America"]
    print(f"\n  Europe+N America+Oceania+E Asia: FD {sh.loc[g1, FD].sum():.1f}%"
          f" -> after protection {sh.loc[g1, FDP].sum():.1f}%")
    print(f"  S Asia+Africa+C America       : FD {sh.loc[g2, FD].sum():.1f}%"
          f" -> after protection {sh.loc[g2, FDP].sum():.1f}%")
    print(f"  (IR-AED: {sh.loc[g2, IR].sum():.1f}% -> {sh.loc[g2, IRP].sum():.1f}%)")

    # ---- Figure 3 distributions -------------------------------------------
    print("\n" + "-" * 74)
    print("Figure 3 - distributions")
    print("-" * 74)
    iqr = lambda s: s.quantile(.75) - s.quantile(.25)
    for lbl, f in (("country", cty), ("FUA", fua)):
        print(f"\n  {lbl} level  (n = {len(f)})")
        for m in METS:
            print(f"    {m:9s} median {pct(f[m].median()):5.2f}%"
                  f"   IQR {pct(iqr(f[m])):4.2f} pp"
                  f"   CV {f[m].std()/f[m].mean()*100:5.1f}%")
        rfd = (1 - f[FDP] / f[FD]).replace([np.inf, -np.inf], np.nan).dropna()
        rir = (1 - f[IRP] / f[IR]).replace([np.inf, -np.inf], np.nan).dropna()
        print(f"    mean protection reduction: FD-AED {rfd.mean()*100:.1f}%,"
              f" IR-AED {rir.mean()*100:.1f}%")
        print(f"    IQR compression by protection: FD-AED {(1-iqr(f[FDP])/iqr(f[FD]))*100:.0f}%,"
              f" IR-AED {(1-iqr(f[IRP])/iqr(f[IR]))*100:.0f}%")

    # ---- Figure 2 tertiles -------------------------------------------------
    print("\n" + "-" * 74)
    print("Figure 2 - tertile movement between FD-AED and IR-AED")
    print("-" * 74)
    v = cty[(cty[FD] > 0) & (cty[IR] > 0)].copy()
    v["t_FD"] = pd.qcut(v[FD], 3, labels=False)
    v["t_IR"] = pd.qcut(v[IR], 3, labels=False)
    v["shift"] = v.t_IR - v.t_FD
    print(f"  countries with valid values: {len(v)}")
    print(f"    move to a LOWER tertile  : {(v['shift'] < 0).sum()}"
          f"   (mean height {v.loc[v['shift'] < 0, 'height_mean'].mean():.1f} m)")
    print(f"    move to a HIGHER tertile : {(v['shift'] > 0).sum()}"
          f"   (mean height {v.loc[v['shift'] > 0, 'height_mean'].mean():.1f} m)")
    print(f"    unchanged                : {(v['shift'] == 0).sum()}")
    two = v[v['shift'].abs() == 2]
    jumps = ", ".join(f"{r.Cntry_name} ({int(r.t_FD)}->{int(r.t_IR)})"
                      for r in two.itertuples()) or "none"
    print(f"    two-tertile jumps: {jumps}")
    print("\n    worsening countries (Medium/Low -> higher), by region:")
    for rg, grp in v[v['shift'] > 0].groupby("wld_rgn"):
        names = ", ".join(f"{r.Cntry_name} ({r.height_mean:.1f} m)"
                          for r in grp.sort_values("height_mean").itertuples())
        print(f"      {rg:10s} {names}")
    print("\n    improving countries (-> lower), by region:")
    for rg, grp in v[v['shift'] < 0].groupby("wld_rgn"):
        names = ", ".join(f"{r.Cntry_name} ({r.height_mean:.1f} m)"
                          for r in grp.sort_values("height_mean").itertuples())
        print(f"      {rg:10s} {names}")

    hi = v[(v.t_FD == 2) & (v.t_IR == 2)]
    print(f"\n    remain in the HIGH tertile under both metrics: {len(hi)}")
    print("      " + ", ".join(sorted(hi.Cntry_name)))
    hi = hi.copy()
    hi["red"] = 1 - hi[FDP] / hi[FD]
    print("\n      best protection benefit:")
    for r in hi.sort_values("red", ascending=False).head(8).itertuples():
        print(f"        {r.Cntry_name:15s} {r.red*100:5.1f}%")
    print("      least protection benefit:")
    for r in hi.sort_values("red").head(8).itertuples():
        print(f"        {r.Cntry_name:15s} {r.red*100:5.1f}%")

    # ---- city-level statements --------------------------------------------
    print("\n" + "-" * 74)
    print("Results 2 - city-level statements")
    print("-" * 74)
    f = fua.copy()
    f["gap"] = f[FD] - f[IR]
    print("\n  largest FD-AED minus IR-AED gaps (tall stock lowers the ratio):")
    for r in f.nlargest(8, "gap").itertuples():
        print(f"    {r.eFUA_name:18s} {r.Cntry_name:12s} FD {pct(getattr(r, FD)):5.2f}%"
              f"  IR {pct(getattr(r, IR)):5.2f}%  h {r.height_mean:5.2f} m")
    print("\n  cities where IR-AED exceeds FD-AED, largest first:")
    ex = f[f[IR] > f[FD]]
    print(f"    n = {len(ex)} of {len(f)}")
    for r in ex.nlargest(8, IR).itertuples():
        print(f"    {r.eFUA_name:18s} {r.Cntry_name:12s} FD {pct(getattr(r, FD)):5.2f}%"
              f"  IR {pct(getattr(r, IR)):5.2f}%  h {r.height_mean:5.2f} m")

    named = ["Cali", "Sao Paulo", "São Paulo", "Rio de Janeiro", "Vila Velha", "Luxor",
             "Wuhan", "Bangkok", "Shanghai", "Dhaka", "Hyderabad", "Long Xuyen",
             "Phnom Penh", "Mandalay", "Hanoi", "Ho Chi Minh City", "N'Djamena",
             "Yichang", "Guangzhou"]
    print("\n  named cities:")
    for nm in named:
        s = f[f.eFUA_name == nm]
        for r in s.itertuples():
            print(f"    {r.eFUA_name:18s} {r.Cntry_name:12s} h {r.height_mean:5.2f} m"
                  f"  FD {pct(getattr(r, FD)):5.2f}% -> {pct(getattr(r, FDP)):5.2f}%"
                  f"  IR {pct(getattr(r, IR)):5.2f}% -> {pct(getattr(r, IRP)):5.2f}%")

    cn = f[f.Cntry_name == "China"]
    red = 1 - cn[FDP] / cn[FD]
    print(f"\n  China: {len(cn)} FUAs, mean FD-AED reduction by protection {red.mean()*100:.0f}%")
    top = cn.assign(red=red).nlargest(5, "red")
    print("    most protected: " + ", ".join(
        f"{r.eFUA_name} ({r.red*100:.0f}%)" for r in top.itertuples()))

    print("\nwrote a4_fua_2026-08.csv, a4_country_2026-08.csv, a4_fig1_panelA_2026-08.csv")


if __name__ == "__main__":
    main()
