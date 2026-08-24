"""
A1 - Building-height dataset sensitivity of IR-AED (Reviewer 4, Comment 5).

Purpose
-------
The manuscript currently characterises IR-AED as showing "moderate sensitivity"
to the building-height dataset (CV = 27.7%) in one place and as "highly
sensitive" in another. Reviewer 4 asks for consistent terminology or a
quantitative basis. This script rebuilds the three-dataset comparison from the
source exports and produces that basis.

Two issues with the original comparison script
(code_deposit/python/compare_building_height_datasets_2026-1-17.py) are fixed
here and reported explicitly so the change is auditable:

  1. It merged the three datasets on `eFUA_name`, which is not unique. Eight
     distinct FUAs are named "Guangzhou", so the three-way merge produced
     8^3 = 512 rows for that city alone; 607 unique names became 1368 rows.
     We merge on `eFUA_ID` instead.
  2. `CV = 27.7%` is the coefficient of variation of the three *dataset-wide
     mean* IR-AED values, not a per-FUA sensitivity. We report both, plus the
     per-FUA distribution and rank correlations.

We also quantify a coverage effect: IR-AED is only defined on pixels where the
building-height dataset reports a height, so `exInunD_count` differs between
datasets. Part of the between-dataset spread is therefore a difference in which
pixels are averaged, not in the height values themselves.

Run:  python a1_height_dataset_sensitivity.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import paths

SRC = paths.FUA_2026_01
OUT = paths.OUTPUT

REGIONS = ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]
DATASETS = ["JRC", "WSF3D", "GBH2020"]

# Metrics we need as per-FUA means. Some regional exports (JRC_Oceania) carry
# only `_sum` and `_count`, so means are derived where absent.
MEAN_COLS = ["height", "exDmg", "exInunD", "exDmg_pros", "exInunD_pros"]


def load_one(dataset: str, region: str) -> pd.DataFrame:
    """Load one dataset-region export, preferring the CORRECTED file."""
    corrected = SRC / f"{dataset}_{region}_FloodRisk_CORRECTED.csv"
    plain = SRC / f"{dataset}_{region}_FloodRisk.csv"
    path = corrected if corrected.exists() else plain

    df = pd.read_csv(path)
    df["source_file"] = path.name
    df["region_file"] = region

    for base in MEAN_COLS:
        mean_col, sum_col, cnt_col = f"{base}_mean", f"{base}_sum", f"{base}_count"
        if mean_col not in df.columns:
            if sum_col in df.columns and cnt_col in df.columns:
                cnt = df[cnt_col].replace(0, np.nan)
                df[mean_col] = df[sum_col] / cnt
            else:
                df[mean_col] = np.nan
        if cnt_col not in df.columns:
            df[cnt_col] = np.nan

    return df


def load_dataset(dataset: str) -> pd.DataFrame:
    frames = [load_one(dataset, r) for r in REGIONS]
    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset="eFUA_ID", keep="first")
    return df


def spearman(a, b):
    mask = np.isfinite(a) & np.isfinite(b)
    return stats.spearmanr(a[mask], b[mask]).statistic, int(mask.sum())


def main() -> None:
    print("=" * 78)
    print("A1  Building-height dataset sensitivity of IR-AED")
    print("=" * 78)

    raw = {ds: load_dataset(ds) for ds in DATASETS}
    for ds in DATASETS:
        print(f"  {ds:8s} unique FUAs = {len(raw[ds])}")

    keep = ["eFUA_ID", "eFUA_name", "Cntry_name", "height_mean", "exDmg_mean",
            "exInunD_mean", "exInunD_count", "exDmg_count"]
    merged = raw["JRC"][keep].rename(columns=lambda c: c + "_jrc" if c not in
                                     ("eFUA_ID", "eFUA_name", "Cntry_name") else c)
    for ds, suf in (("WSF3D", "_wsf3d"), ("GBH2020", "_gbh")):
        right = raw[ds][["eFUA_ID", "height_mean", "exDmg_mean", "exInunD_mean",
                         "exInunD_count", "exDmg_count"]]
        right = right.rename(columns=lambda c: c + suf if c != "eFUA_ID" else c)
        merged = merged.merge(right, on="eFUA_ID", how="inner")

    ir_cols = ["exInunD_mean_jrc", "exInunD_mean_wsf3d", "exInunD_mean_gbh"]
    h_cols = ["height_mean_jrc", "height_mean_wsf3d", "height_mean_gbh"]

    clean = merged.dropna(subset=ir_cols + h_cols).copy()
    # Drop FUAs with no modelled inundation anywhere: a CV is undefined there.
    clean = clean[clean[ir_cols].sum(axis=1) > 0].copy()

    print(f"\n  FUAs present in all three datasets            : {len(merged)}")
    print(f"  ...with finite height and IR-AED in all three : {len(clean)}")
    clean.to_csv(paths.out("a1_comparison_by_eFUA_ID.csv"), index=False)

    # ---- 1. Dataset-wide means (the basis of the manuscript's 27.7% CV) ----
    print("\n" + "-" * 78)
    print("1. Dataset-wide means (mean of FUA means), merged on eFUA_ID")
    print("-" * 78)

    def between_dataset_cv(cols):
        means = np.array([clean[c].mean() for c in cols])
        return means, means.std(ddof=0) / means.mean() * 100

    h_means, h_cv = between_dataset_cv(h_cols)
    ir_means, ir_cv = between_dataset_cv(ir_cols)
    fd_means, fd_cv = between_dataset_cv(
        ["exDmg_mean_jrc", "exDmg_mean_wsf3d", "exDmg_mean_gbh"])

    print(f"  Building height (m)  JRC {h_means[0]:6.2f}  WSF3D {h_means[1]:6.2f}"
          f"  GBH2020 {h_means[2]:6.2f}   between-dataset CV = {h_cv:5.1f}%")
    print(f"  FD-AED (%)           JRC {fd_means[0]*100:6.2f}  WSF3D {fd_means[1]*100:6.2f}"
          f"  GBH2020 {fd_means[2]*100:6.2f}   between-dataset CV = {fd_cv:5.1f}%")
    print(f"  IR-AED (%)           JRC {ir_means[0]*100:6.2f}  WSF3D {ir_means[1]*100:6.2f}"
          f"  GBH2020 {ir_means[2]*100:6.2f}   between-dataset CV = {ir_cv:5.1f}%")

    # ---- 2. Per-FUA CV: the sensitivity an individual city actually faces ----
    print("\n" + "-" * 78)
    print("2. Per-FUA coefficient of variation of IR-AED across the 3 datasets")
    print("-" * 78)

    vals = clean[ir_cols].to_numpy()
    per_fua_cv = vals.std(axis=1, ddof=0) / vals.mean(axis=1) * 100
    q = np.percentile(per_fua_cv, [10, 25, 50, 75, 90])
    print(f"  n = {len(per_fua_cv)} FUAs")
    print(f"  median = {np.median(per_fua_cv):.1f}%   IQR = {q[1]:.1f}-{q[3]:.1f}%"
          f"   P10-P90 = {q[0]:.1f}-{q[4]:.1f}%   mean = {per_fua_cv.mean():.1f}%")
    print(f"  share of FUAs with CV > 50%: "
          f"{(per_fua_cv > 50).mean()*100:.1f}%")

    # ---- 3. Pairwise agreement in level and in rank ----
    print("\n" + "-" * 78)
    print("3. Pairwise agreement between datasets (IR-AED)")
    print("-" * 78)
    pairs = [("JRC", "WSF3D", "exInunD_mean_jrc", "exInunD_mean_wsf3d"),
             ("JRC", "GBH2020", "exInunD_mean_jrc", "exInunD_mean_gbh"),
             ("WSF3D", "GBH2020", "exInunD_mean_wsf3d", "exInunD_mean_gbh")]
    for a, b, ca, cb in pairs:
        x, y = clean[ca].to_numpy(), clean[cb].to_numpy()
        rel_mean_diff = (y.mean() - x.mean()) / x.mean() * 100
        denom = (np.abs(x) + np.abs(y)) / 2
        smape = np.median(np.abs(y - x) / np.where(denom > 0, denom, np.nan)) * 100
        rho, n = spearman(x, y)
        print(f"  {a:8s} vs {b:8s}  mean level diff = {rel_mean_diff:+7.1f}%"
              f"   median |rel. diff| = {smape:5.1f}%   Spearman rho = {rho:.3f} (n={n})")

    # ---- 4. Coverage effect: IR-AED is defined on different pixel sets ----
    print("\n" + "-" * 78)
    print("4. Coverage: pixels contributing to IR-AED vs FD-AED")
    print("-" * 78)
    for ds, suf in (("JRC", "_jrc"), ("WSF3D", "_wsf3d"), ("GBH2020", "_gbh")):
        ir_n = clean["exInunD_count" + suf].to_numpy(dtype=float)
        fd_n = clean["exDmg_count" + suf].to_numpy(dtype=float)
        ratio = np.where(fd_n > 0, ir_n / fd_n, np.nan) * 100
        print(f"  {ds:8s} median IR-AED pixels as share of FD-AED pixels ="
              f" {np.nanmedian(ratio):5.1f}%   (total IR pixels = {np.nansum(ir_n):,.0f})")

    # ---- 5. Reproduce the flawed name-merge, for the response letter ----
    print("\n" + "-" * 78)
    print("5. Effect of the original eFUA_name merge (for disclosure)")
    print("-" * 78)
    name_merge = raw["JRC"][["eFUA_name", "height_mean", "exInunD_mean"]]
    for ds, suf in (("WSF3D", "_wsf3d"), ("GBH2020", "_gbh")):
        r = raw[ds][["eFUA_name", "height_mean", "exInunD_mean"]]
        r = r.rename(columns=lambda c: c + suf if c != "eFUA_name" else c)
        name_merge = name_merge.merge(r, on="eFUA_name", how="inner")
    name_merge = name_merge.dropna()
    print(f"  rows after name-merge = {len(name_merge)} "
          f"(vs {len(clean)} unique FUAs)")
    nm_ir = np.array([name_merge["exInunD_mean"].mean(),
                      name_merge["exInunD_mean_wsf3d"].mean(),
                      name_merge["exInunD_mean_gbh"].mean()])
    print(f"  name-merge IR-AED means (%) = {nm_ir*100}")
    print(f"  name-merge between-dataset CV = "
          f"{nm_ir.std(ddof=0)/nm_ir.mean()*100:.1f}%")

    summary = pd.DataFrame({
        "metric": ["Building height (m)", "FD-AED (%)", "IR-AED (%)"],
        "JRC": [h_means[0], fd_means[0] * 100, ir_means[0] * 100],
        "WSF3D": [h_means[1], fd_means[1] * 100, ir_means[1] * 100],
        "GBH2020": [h_means[2], fd_means[2] * 100, ir_means[2] * 100],
        "between_dataset_CV_pct": [h_cv, fd_cv, ir_cv],
    })
    summary.to_csv(paths.out("a1_height_sensitivity_summary_2026-08.csv"), index=False)
    pd.DataFrame({"eFUA_ID": clean["eFUA_ID"], "eFUA_name": clean["eFUA_name"],
                  "Cntry_name": clean["Cntry_name"],
                  "per_fua_cv_pct": per_fua_cv}).to_csv(
        paths.out("a1_height_sensitivity_per_fua_2026-08.csv"), index=False)

    print("\nWrote a1_summary.csv, a1_per_fua_cv.csv, a1_comparison_by_eFUA_ID.csv")


if __name__ == "__main__":
    main()
