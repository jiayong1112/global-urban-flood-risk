"""
A6 - Every Results-section statistic, recomputed on the 2026-08 export.

Consumes a5_fua_2026-08.csv / a5_country_2026-08.csv (see a5_assemble_2026-08.py).

Indicator conventions, matching the Methods:
  FD-AED   exDmg_mean       modelled floodplain
  IR-AED   exInunD_mean     built-up floodplain
  FD-AED-P exDmg_pros_mean  as above, restricted to pixels with a FLOPROS record
  IR-AED-P exInunD_pros_mean
Protection *reductions* are always computed against the _cmp bands, i.e. the
unprotected metric on the same FLOPROS pixels, so no reduction is contaminated
by the change of domain.

The script also reports what changes if the unprotected indicators are placed on
the FLOPROS domain too, so that the choice can be checked rather than assumed.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
sys.path.insert(0, str(BASE / "revision-2026-08" / "figures"))
from region_map import REGION_MAP  # noqa: E402

FD, FDP, FDC = "exDmg_mean", "exDmg_pros_mean", "exDmg_cmp_mean"
IR, IRP, IRC = "exInunD_mean", "exInunD_pros_mean", "exInunD_cmp_mean"

fua = pd.read_csv(HERE / "a5_fua_2026-08.csv")
cty = pd.read_csv(HERE / "a5_country_2026-08.csv")
iqr = lambda s: s.quantile(.75) - s.quantile(.25)
pc = lambda x: 100 * x


def shares(frame, cols, key="Cntry_name"):
    """FUA -> country mean -> region mean -> share of global, as in Figure 1a."""
    c = frame.groupby([key, "wld_rgn"])[cols].mean().reset_index()
    r = c.groupby("wld_rgn")[cols].mean()
    return 100 * r / r.sum()


print("=" * 78)
print("SAMPLE")
print("=" * 78)
print(f"  {len(fua)} FUAs, {len(cty)} countries, {fua.wld_rgn.nunique()} regions")
valid = fua[[FD, IR, FDP, IRP]].notna().all(axis=1)
print(f"  {int(valid.sum())} FUAs carry all four indicators")

print()
print("=" * 78)
print("FIGURE 1a  - share of global total (%)")
print("=" * 78)
sh = shares(fua, [FD, IR, FDP, IRP])
sh.columns = ["FD", "IR", "FD_P", "IR_P"]
out = sh.copy()
out["IR_vs_FD_%"] = (sh.IR - sh.FD) / sh.FD * 100
print(out.round(2).to_string())
sh.round(4).to_csv(HERE / "a6_fig1_panelA_2026-08.csv")

alt = shares(fua, [FDC, IRC, FDP, IRP])
alt.columns = ["FD", "IR", "FD_P", "IR_P"]
print("\n  if the unprotected indicators are placed on the FLOPROS domain too:")
print((alt[["FD", "IR"]] - sh[["FD", "IR"]]).round(3).to_string())
print(f"  max shift {float((alt[['FD','IR']] - sh[['FD','IR']]).abs().max().max()):.3f} pp")

g1 = ["Europe", "N America", "Oceania", "E Asia"]
g2 = ["S Asia", "Africa", "C America"]
print(f"\n  Europe+N America+Oceania+E Asia: FD {sh.loc[g1,'FD'].sum():.1f}%"
      f" -> {sh.loc[g1,'FD_P'].sum():.1f}%")
print(f"  S Asia+Africa+C America       : FD {sh.loc[g2,'FD'].sum():.1f}%"
      f" -> {sh.loc[g2,'FD_P'].sum():.1f}%   IR {sh.loc[g2,'IR'].sum():.1f}%"
      f" -> {sh.loc[g2,'IR_P'].sum():.1f}%")
for r in ["Africa", "Europe", "C America", "S America", "SW Asia", "S Asia",
          "Oceania", "E Asia", "N America"]:
    print(f"    {r:10s} FD {sh.FD[r]:5.2f} -> IR {sh.IR[r]:5.2f}"
          f"  ({(sh.IR[r]-sh.FD[r])/sh.FD[r]*100:+.0f}% rel;"
          f" depth-only {(sh.FD[r]-sh.IR[r])/sh.IR[r]*100:+.0f}% of IR)"
          f"   FD_P {sh.FD_P[r]:5.2f}")

print()
print("=" * 78)
print("FIGURE 3  - distributions")
print("=" * 78)
for lbl, f in (("country", cty), ("FUA", fua)):
    print(f"\n  {lbl} level (n = {len(f)})")
    for m, nm in ((FD, "FD-AED"), (FDP, "FD-AED-P"), (IR, "IR-AED"), (IRP, "IR-AED-P")):
        s = f[m].dropna()
        print(f"    {nm:9s} median {pc(s.median()):5.2f}%  IQR {pc(iqr(s)):4.2f} pp"
              f"  CV {s.std()/s.mean()*100:5.1f}%")
    for pre, post, nm in ((FDC, FDP, "FD-AED"), (IRC, IRP, "IR-AED")):
        red = (1 - f[post] / f[pre]).replace([np.inf, -np.inf], np.nan).dropna()
        print(f"    {nm} mean protection reduction {red.mean()*100:.1f}%"
              f"   IQR compression {(1 - iqr(f[post].dropna())/iqr(f[pre].dropna()))*100:.0f}%")

print()
print("=" * 78)
print("FIGURE 2  - tertiles")
print("=" * 78)
v = cty[(cty[FD] > 0) & (cty[IR] > 0)].dropna(subset=[FD, IR]).copy()
v["t_FD"] = pd.qcut(v[FD], 3, labels=False)
v["t_IR"] = pd.qcut(v[IR], 3, labels=False)
v["shift"] = v.t_IR - v.t_FD
lo, hi, sm = v["shift"] < 0, v["shift"] > 0, v["shift"] == 0
print(f"  valid {len(v)}   lower {lo.sum()} (FUA-wide mean height {v.loc[lo,'height_mean'].mean():.1f} m)"
      f"   higher {hi.sum()} ({v.loc[hi,'height_mean'].mean():.1f} m)   same {sm.sum()}")
two = v[v["shift"].abs() == 2]
print("  two-tertile jumps: " + (", ".join(
    f"{r.country_na} ({int(r.t_FD)}->{int(r.t_IR)})" for r in two.itertuples()) or "none"))
for rgn, lab in ((hi, "worsening"), (lo, "improving")):
    print(f"\n  {lab}:")
    for rg, grp in v[rgn].groupby("wld_rgn"):
        print(f"    {rg:10s} " + ", ".join(
            f"{r.country_na} ({r.height_mean:.1f})"
            for r in grp.sort_values("height_mean").itertuples()))
both = v[(v.t_FD == 2) & (v.t_IR == 2)].copy()
both["red"] = 1 - both[FDP] / both[FDC]
print(f"\n  high under both: {len(both)}")
print("    " + ", ".join(sorted(both.country_na)))
print("    best:  " + ", ".join(f"{r.country_na} ({r.red*100:.0f}%)"
                                for r in both.nlargest(6, "red").itertuples()))
print("    least: " + ", ".join(f"{r.country_na} ({r.red*100:.0f}%)"
                                for r in both.nsmallest(6, "red").itertuples()))

print()
print("=" * 78)
print("CITY-LEVEL STATEMENTS")
print("=" * 78)
f = fua.copy()
f["gap"] = f[FD] - f[IR]
print("  largest FD-AED minus IR-AED gaps:")
for r in f.nlargest(6, "gap").itertuples():
    print(f"    {r.eFUA_name:18s} {r.Cntry_name:12s} FD {pc(getattr(r,FD)):5.2f}%"
          f"  IR {pc(getattr(r,IR)):5.2f}%  h {r.height_mean:5.2f} m")
for nm in ["Cali", "São Paulo", "Luxor", "Wuhan", "Bangkok", "Mexico City",
           "Kinshasa", "Niamey", "Mandalay", "Ho Chi Minh City"]:
    for r in f[f.eFUA_name == nm].itertuples():
        red = 1 - getattr(r, FDP) / getattr(r, FDC) if getattr(r, FDC) else np.nan
        print(f"    {r.eFUA_name:18s} {r.Cntry_name:12s} h {r.height_mean:5.2f} m"
              f"  FD {pc(getattr(r,FD)):5.2f}% -> {pc(getattr(r,FDP)):5.2f}%"
              f"  IR {pc(getattr(r,IR)):5.2f}% -> {pc(getattr(r,IRP)):5.2f}%"
              f"  (FD reduction {red*100:.0f}%)")
cn = f[f.Cntry_name == "China"]
red = (1 - cn[FDP] / cn[FDC]).dropna()
print(f"\n  China: {len(cn)} FUAs, mean FD-AED reduction {red.mean()*100:.0f}%")
print("    most protected: " + ", ".join(
    f"{r.eFUA_name} ({r.red*100:.0f}%)"
    for r in cn.assign(red=1 - cn[FDP] / cn[FDC]).nlargest(3, "red").itertuples()))

print()
print("=" * 78)
print("LIKE-FOR-LIKE DOMAIN CHECK (IR-AED vs FD-AED)")
print("=" * 78)
print("  the built-up-domain recomputation is reported in Table S7; here the")
print("  ratio is formed on each indicator's own domain, as reported in the text")
ok = (f[FD] > 0) & (f[IR] > 0)
print(f"  IR-AED / FD-AED across FUAs: median {(f.loc[ok, IR]/f.loc[ok, FD]).median():.3f}")
reg = f[ok].groupby("wld_rgn").apply(
    lambda x: pd.Series({"n": len(x),
                         "IR_over_FD": (x[IR] / x[FD]).mean(),
                         "height_fua": x.height_mean.mean(),
                         "height_fp": x.height_fp_mean.mean()}), include_groups=False)
print(reg.sort_values("height_fp").round(3).to_string())
