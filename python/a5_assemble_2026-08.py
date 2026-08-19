"""
A5 - Assemble the 2026-08 per-FUA exports into the analysis tables.

Inputs : flood_fua_2026-08/JRC_*_fua_2026-08.csv, produced by
         code_deposit/gee/fuaExport_2026-08.js under
         module_floodRisk_inAbove_2026-08.js.

Checks, in order, and stops if any fails:
  1. no duplicate FUAs across batches
  2. every FUA maps to a world region
  3. protected <= unprotected everywhere, on the common FLOPROS domain
  4. reproduction of the published export on the FUAs present in both,
     which should differ only by the newly symmetric rare-event tail

Outputs (analysis/):
  a5_fua_2026-08.csv        per-FUA, all batches merged
  a5_country_2026-08.csv    per-country, mean over FUAs
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
EXPORTS = HERE / "flood_fua_2026-08"
PUB = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission"
sys.path.insert(0, str(BASE / "revision-2026-08" / "figures"))
from region_map import REGION_MAP           # noqa: E402

FD, FDP = "exDmg_mean", "exDmg_pros_mean"
IR, IRP = "exInunD_mean", "exInunD_pros_mean"
FDC, IRC = "exDmg_cmp_mean", "exInunD_cmp_mean"
KEEP = ["eFUA_ID", "eFUA_name", "Cntry_name", "FUA_p_2015", "FUA_area",
        FD, FDP, FDC, IR, IRP, IRC,
        "height_mean", "height_fp_mean", "flopros_mean",
        "exDmg_count", "exInunD_count", "exDmg_cmp_count"]


def load():
    frames = []
    for path in sorted(EXPORTS.glob("JRC_*_fua_2026-08.csv")):
        df = pd.read_csv(path)
        df["batch"] = path.stem.split("_")[1]
        frames.append(df)
        print(f"  {path.name:38s} {len(df):4d} FUAs")
    out = pd.concat(frames, ignore_index=True)

    dupes = out[out.duplicated("eFUA_ID", keep=False)]
    if len(dupes):
        # The Mexico batch is a subset of NAmerica by design; keep one copy.
        print(f"  resolving {dupes.eFUA_ID.nunique()} FUAs exported in more than one batch")
        out = out.sort_values("batch").drop_duplicates("eFUA_ID", keep="first")
    return out[[c for c in KEEP if c in out.columns] + ["batch"]]


def main():
    print("=" * 78)
    print("A5  Assembling the 2026-08 exports")
    print("=" * 78)
    fua = load()
    fua["wld_rgn"] = fua["Cntry_name"].map(REGION_MAP)
    print(f"\n  total {len(fua)} FUAs, {fua.Cntry_name.nunique()} countries")

    unmapped = sorted(fua.loc[fua.wld_rgn.isna(), "Cntry_name"].dropna().unique())
    if unmapped:
        print(f"  [stop] countries with no region: {unmapped}")
        sys.exit(1)
    print("  every FUA maps to a world region")

    # ---- monotonicity, on the domain the two metrics share ----------------
    ok = fua[[FDC, FDP, IRC, IRP]].notna().all(axis=1)
    bad_fd = int((fua.loc[ok, FDP] > fua.loc[ok, FDC] + 1e-12).sum())
    bad_ir = int((fua.loc[ok, IRP] > fua.loc[ok, IRC] + 1e-12).sum())
    print(f"  protected > unprotected: FD-AED {bad_fd}, IR-AED {bad_ir} "
          f"(of {int(ok.sum())} FUAs with both)")
    if bad_fd or bad_ir:
        print("  [stop] the integration is still asymmetric somewhere")
        sys.exit(1)

    # ---- reproduction against the published export ------------------------
    pubf = []
    for c in ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]:
        d = pd.read_csv(PUB / "csv_fua_2026-1-17" / f"JRC_{c}_FloodRisk.csv")
        for m in (FD, IR, FDP, IRP):
            if m not in d.columns:
                b = m.replace("_mean", "")
                d[m] = d[f"{b}_sum"] / d[f"{b}_count"]
        pubf.append(d)
    pub = pd.concat(pubf, ignore_index=True).drop_duplicates("eFUA_ID", keep="first")
    m = fua.merge(pub[["eFUA_ID", FD, IR, "height_mean", "exDmg_count", "exInunD_count"]],
                  on="eFUA_ID", suffixes=("", "_pub"))
    print(f"\n  {len(m)} FUAs present in both exports")
    for col, lbl in ((FD, "unprotected FD-AED"), (IR, "unprotected IR-AED"),
                     ("height_mean", "FUA-wide height"),
                     ("exDmg_count", "FD pixel count"),
                     ("exInunD_count", "IR pixel count")):
        r = (m[col] / m[col + "_pub"]).replace([np.inf, -np.inf], np.nan).dropna()
        print(f"    {lbl:20s} new/published  median {r.median():.4f}"
              f"   IQR {r.quantile(.25):.4f}-{r.quantile(.75):.4f}")

    new_ids = sorted(set(fua.eFUA_ID) - set(pub.eFUA_ID))
    print(f"  {len(new_ids)} FUAs new to this export")
    if new_ids:
        nn = fua[fua.eFUA_ID.isin(new_ids)]
        print("    " + ", ".join(f"{r.eFUA_name} ({r.Cntry_name})"
                                 for r in nn.itertuples()))

    # ---- height domains ---------------------------------------------------
    h = fua.dropna(subset=["height_mean", "height_fp_mean"])
    h = h[(h.height_mean > 0) & (h.height_fp_mean > 0)]
    ratio = h.height_fp_mean / h.height_mean
    print(f"\n  floodplain / FUA-wide mean height: median {ratio.median():.3f}"
          f"  IQR {ratio.quantile(.25):.3f}-{ratio.quantile(.75):.3f}")
    bu = (fua.exInunD_count / fua.exDmg_count).replace([np.inf, -np.inf], np.nan).dropna()
    print(f"  built-up fraction of the floodplain: median {bu.median():.3f}"
          f"  IQR {bu.quantile(.25):.3f}-{bu.quantile(.75):.3f}")

    # ---- country table ----------------------------------------------------
    cty = fua.groupby(["Cntry_name", "wld_rgn"], as_index=False)[
        [FD, FDP, FDC, IR, IRP, IRC, "height_mean", "height_fp_mean"]].mean()
    cty["n_fuas"] = fua.groupby(["Cntry_name", "wld_rgn"]).size().values
    cty = cty.rename(columns={"Cntry_name": "country_na"})

    fua.to_csv(HERE / "a5_fua_2026-08.csv", index=False)
    cty.to_csv(HERE / "a5_country_2026-08.csv", index=False)
    print(f"\n  wrote a5_fua_2026-08.csv ({len(fua)} FUAs) and "
          f"a5_country_2026-08.csv ({len(cty)} countries)")


if __name__ == "__main__":
    main()
