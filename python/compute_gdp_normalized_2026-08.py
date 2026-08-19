"""
GDP-weighted and GDP-normalized flood losses, third revision (August 2026).

Identical in method to code/figures/compute_gdp_normalized_2026-7.py. The only
change is the region mapping, which now places Russia in Europe (see
region_map_2026-08.py).

The script runs twice: once with the previously published mapping, to confirm
it reproduces data/gdp_normalized_region_2026-7.csv exactly, and once with the
corrected mapping, which is what the revised figures use.

Outputs (revision-2026-08/figures/):
  gdp_normalized_region_2026-08.csv
  gdp_normalized_country_2026-08.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from region_map import REGION_MAP, PUBLISHED_REGION_MAP

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
SRC = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission" / "csv_fua_2026-1-17"
TOTALGDP_CSV = BASE / "data" / "fua_totalGDP_2026-7.csv"
PUBLISHED_REGION_CSV = BASE / "data" / "gdp_normalized_region_2026-7.csv"

CONTINENTS = ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]
METRICS = ["exDmg_sum", "exDmg_pros_sum", "exInunD_sum", "exInunD_pros_sum"]


def load_merged():
    frames = []
    for c in CONTINENTS:
        frames.append(pd.read_csv(SRC / f"JRC_{c}_GDP.csv"))
    gdp = pd.concat(frames, ignore_index=True).drop_duplicates("eFUA_ID", keep="first")

    tot = pd.read_csv(TOTALGDP_CSV)[["eFUA_ID", "sum"]]
    tot = tot.rename(columns={"sum": "totalGDP"}).drop_duplicates("eFUA_ID", keep="first")
    m = gdp.merge(tot, on="eFUA_ID", how="left", validate="1:1")
    return m[m["totalGDP"] > 0].copy()


def region_table(m, mapping):
    d = m.copy()
    d["wld_rgn"] = d["Cntry_name"].map(mapping)
    d = d.dropna(subset=["wld_rgn"])
    reg = d.groupby("wld_rgn")[METRICS + ["totalGDP"]].sum()
    reg["n_fuas"] = d.groupby("wld_rgn").size()
    for met in METRICS:
        reg[met.replace("_sum", "_bnUSD")] = reg[met] / 1e9
        reg[met.replace("_sum", "_share_pct")] = 100 * reg[met] / reg[met].sum()
        reg[met.replace("_sum", "_pctGDP")] = 100 * reg[met] / reg["totalGDP"]
    reg["totalGDP_bnUSD"] = reg["totalGDP"] / 1e9
    cols = (["n_fuas", "totalGDP_bnUSD"]
            + [met.replace("_sum", s) for met in METRICS
               for s in ("_bnUSD", "_share_pct", "_pctGDP")])
    return reg[cols].round(4), d


def main():
    m = load_merged()
    print(f"FUAs with positive total GDP: {len(m)}")

    # ---- reproduction check against the previously submitted table ---------
    old, _ = region_table(m, PUBLISHED_REGION_MAP)
    ref = pd.read_csv(PUBLISHED_REGION_CSV, index_col=0)
    shared = [c for c in old.columns if c in ref.columns]
    diff = (old[shared] - ref[shared]).abs().max().max()
    print(f"reproduction of gdp_normalized_region_2026-7.csv: max abs diff = {diff:.6g}")
    if diff > 1e-3:
        raise SystemExit("published GDP table not reproduced - stop and investigate")

    # ---- corrected mapping -------------------------------------------------
    newr, d = region_table(m, REGION_MAP)
    newr.to_csv(HERE / "gdp_normalized_region_2026-08.csv")

    cty = d.groupby(["Cntry_name", "wld_rgn"])[METRICS + ["totalGDP"]].sum().reset_index()
    for met in METRICS:
        cty[met.replace("_sum", "_pctGDP")] = 100 * cty[met] / cty["totalGDP"]
    cty.round(6).to_csv(HERE / "gdp_normalized_country_2026-08.csv", index=False)

    print("\n=== GDP-weighted expected loss, corrected mapping ===")
    print(newr[["n_fuas", "exDmg_bnUSD", "exDmg_share_pct",
                "exInunD_share_pct"]].sort_values("exDmg_bnUSD", ascending=False)
          .round(2).to_string())

    print("\n=== Loss as % of regional urban GDP ===")
    print(newr[["exDmg_pctGDP", "exInunD_pctGDP",
                "exDmg_pros_pctGDP", "exInunD_pros_pctGDP"]].round(3).to_string())

    def share(col, regions, table):
        return 100 * table.loc[table.index.isin(regions), col].sum() / table[col].sum()

    well = ["Europe", "N America", "Oceania", "E Asia"]
    poor = ["S Asia", "SE Asia", "Africa"]
    print("\n=== GDP-weighted shares: published mapping -> corrected mapping ===")
    for lbl, col, grp in [
            ("Africa FD-AED", "exDmg_bnUSD", ["Africa"]),
            ("Africa IR-AED", "exInunD_bnUSD", ["Africa"]),
            ("Europe FD-AED", "exDmg_bnUSD", ["Europe"]),
            ("Europe IR-AED", "exInunD_bnUSD", ["Europe"]),
            ("S Asia FD-AED", "exDmg_bnUSD", ["S Asia"]),
            ("S Asia IR-AED", "exInunD_bnUSD", ["S Asia"]),
            ("E Asia FD-AED", "exDmg_bnUSD", ["E Asia"]),
            ("E Asia IR-AED", "exInunD_bnUSD", ["E Asia"]),
            ("well-protected 4, FD", "exDmg_bnUSD", well),
            ("well-protected 4, FD-P", "exDmg_pros_bnUSD", well),
            ("S+SE Asia+Africa, FD", "exDmg_bnUSD", poor),
            ("S+SE Asia+Africa, FD-P", "exDmg_pros_bnUSD", poor)]:
        print(f"  {lbl:24s} {share(col, grp, old):5.1f}%  ->  {share(col, grp, newr):5.1f}%")

    print(f"\nwrote {HERE / 'gdp_normalized_region_2026-08.csv'}")


if __name__ == "__main__":
    main()
