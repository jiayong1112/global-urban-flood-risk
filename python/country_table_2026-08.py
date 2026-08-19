"""
Country-level table, third revision (August 2026).

The previously submitted country table (fua_world_countries_2026-1-8.csv, 108
countries) omits 18 countries that have functional urban areas in the analysis
and are listed in Table S2. This script extends it with those countries,
computing each as the plain mean over its FUAs — the same aggregation the
published table uses (verified: plain FUA means reproduce the published country
values to ~1.3% mean relative error, whereas pixel-count-weighted means differ
by ~5%).

Two provenance notes, carried in the output for transparency:
  * the 108 original countries keep their published values, from the 2026-1-8
    export; the 18 added countries are computed from the 2026-1-17 per-FUA
    export. The two exports differ by ~1.3% on shared countries.
  * the 2026-1-17 per-FUA export is missing 8 Mexican FUAs (Mexico City,
    Guadalajara, Puebla, Toluca, Leon, Queretaro, Aguascalientes, Cuernavaca)
    that the 2026-1-8 country table includes. Mexico therefore keeps its
    published country value, based on 14 FUAs, and is flagged below.

Output: country_table_2026-08.csv  (126 countries)
"""

from pathlib import Path

import pandas as pd

from region_map import REGION_MAP

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
SUB = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission"
SRC = SUB / "csv_fua_2026-1-17"

METS = ["exDmg_mean", "exDmg_pros_mean", "exInunD_mean", "exInunD_pros_mean"]


def load_fua():
    frames = []
    for c in ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]:
        df = pd.read_csv(SRC / f"JRC_{c}_FloodRisk.csv")
        for m in METS:
            if m not in df.columns:
                b = m.replace("_mean", "")
                df[m] = df[f"{b}_sum"] / df[f"{b}_count"]
        frames.append(df)
    return pd.concat(frames, ignore_index=True).drop_duplicates("eFUA_ID", keep="first")


def main():
    fua = load_fua()
    pub = pd.read_csv(SUB / "fua_world_countries_2026-1-8.csv")
    pub["source"] = "2026-1-8 (published)"

    have = set(pub.country_na)
    add_names = sorted(set(fua.Cntry_name) - have)
    add_src = fua[fua.Cntry_name.isin(add_names)]

    add = add_src.groupby("Cntry_name")[METS + ["height_mean"]].mean().reset_index()
    add["n_fuas"] = add_src.groupby("Cntry_name").size().values
    add = add.rename(columns={"Cntry_name": "country_na"})
    add["source"] = "2026-1-17 (added)"

    out = pd.concat([pub, add], ignore_index=True)
    out["wld_rgn"] = out["country_na"].map(REGION_MAP)
    unmapped = sorted(out.loc[out.wld_rgn.isna(), "country_na"])
    if unmapped:
        print(f"[warn] still unmapped: {unmapped}")

    out = out.dropna(subset=["wld_rgn"])
    out.to_csv(HERE / "country_table_2026-08.csv", index=False)

    print(f"countries: {len(pub)} published + {len(add)} added = {len(out)}")
    print(f"added: {', '.join(add.country_na)}")
    print(f"total FUAs represented: {int(out.n_fuas.sum())}")
    print("\nregion counts:")
    print(out.wld_rgn.value_counts().to_string())

    mx_fua = int((fua.Cntry_name == "Mexico").sum())
    mx_tab = int(pub.loc[pub.country_na == "Mexico", "n_fuas"].iloc[0])
    print(f"\n[note] Mexico: country table {mx_tab} FUAs, per-FUA export {mx_fua} FUAs "
          f"({mx_tab - mx_fua} missing from the per-FUA export, including Mexico City)")


if __name__ == "__main__":
    main()
