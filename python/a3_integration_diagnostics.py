"""
A3 - Integration diagnostics, protection discretisation, and alpha sensitivity.

Consumes the Earth Engine exports produced by
  gee/STAGE1_diagnostics_toAsset_2026-08.js and
  gee/STAGE2_diagnostics_fuaExport_2026-08.js
which must be downloaded to
  exports/csv_fua_diag_2026-08/<HEIGHT>_<REGION>_diag_2026-08.csv

Answers, with numbers:

  R4 Comment 2 - probabilities outside the 10-500 yr maps
      * share of AED contributed by each of the five trapezoid bands
      * size of the omitted rare tail (p < 0.002), measured rather than bounded
      * bracket on the omitted frequent range (p > 0.1)
      * effect of harmonising the tail between protected and unprotected metrics,
        including whether any FUA still shows protected AED > unprotected AED

  R4 Comment 2 (cont.) - protection snapped up vs down to a mapped return period

  R3 Comment 3 - stability of results under R_alpha = min(d/h,1)^alpha,
      alpha in {0.5, 1, 2}

  R4 Comment 5 - three-dataset height sensitivity, recomputed with the WSF3D
      decimetre-to-metre fix applied consistently to heights AND to IR-AED

Run:  python a3_integration_diagnostics.py
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import stats

import paths

DIAG = paths.DIAG_2026_08

# Unzipping a Drive download often nests the folder inside itself; descend if so.
if (DIAG / DIAG.name).is_dir():
    DIAG = DIAG / DIAG.name

REGIONS = ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]
DATASETS = ["JRC", "WSF3D", "GBH2020"]

# Trapezoid bands, rarest first: (rarer RP, more frequent RP, delta p)
BANDS = [("500", "200", 0.003), ("200", "100", 0.005), ("100", "50", 0.010),
         ("50", "20", 0.030), ("20", "10", 0.050)]

P_MIN_MAPPED = 0.002   # AEP of the 500-yr map
P_MAX_MAPPED = 0.100   # AEP of the 10-yr map


# The Earth Engine export does not carry wld_rgn, so world regions are derived
# from country names using the single authoritative mapping in region_map.py.
# That module is shared with combine_fua_data.py and the figure scripts; it
# assigns Russia to Europe, matching Table S2. An inlined copy here placed
# Russia in Central Asia and changed every regional row of Tables S5 and S7.
from region_map import REGION_MAP


def load(dataset: str) -> pd.DataFrame:
    """
    Read every export for a dataset and reassemble it into one table.

    Accepts all three export layouts, mixed freely in the same folder:
      v1  JRC_Asia_diag_2026-08.csv              macro-region, all bands
      v2  JRC_EAsia_diag_2026-08.csv             LSIB sub-region, all bands
      v3  JRC_EAsia_core_c0_diag_2026-08.csv     sub-region, band group, chunk

    Chunks contribute disjoint rows; band groups contribute different columns
    for the same rows. Both are handled by concatenating everything and then
    collapsing on eFUA_ID, taking the first non-null value in each column.
    """
    # Recurse: later batches were downloaded into subfolders (e.g. more_FUAs/).
    paths = sorted(DIAG.rglob(f"{dataset}_*_diag_2026-08.csv"))
    if not paths:
        print(f"  [missing] no {dataset}_*_diag_2026-08.csv under {DIAG.name}")
        return pd.DataFrame()

    frames = []
    for path in paths:
        df = pd.read_csv(path)
        df = df.drop(columns=[c for c in ("system:index", ".geo") if c in df.columns])
        df["region_file"] = path.stem.split("_")[1]
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    n_raw = len(out)

    # A FUA can appear in more than one region's export. Stage 2b selects
    # features with filterBounds against the asset footprint, which also catches
    # neighbours that merely touch the union boundary; those rows are computed
    # from a sliver of the FUA and, worse, with the neighbouring region's
    # depth-damage curve. The row where the FUA sits wholly inside the region has
    # the most contributing pixels, so sort by pixel count descending before
    # collapsing. groupby.first() then takes the first non-null per column, which
    # means the fullest row wins for every column it carries, while band-group
    # files (no pixel count, sorted last) still supply the columns only they have.
    if "exDmg_count" in out.columns:
        out["_rank"] = out["exDmg_count"].fillna(-1)
    else:
        out["_rank"] = -1
    out = out.sort_values("_rank", ascending=False)

    dupes = int(out["eFUA_ID"].duplicated().sum())
    out = out.groupby("eFUA_ID", as_index=False).first().drop(columns="_rank")

    print(f"  {dataset:8s} read {len(paths)} file(s), {n_raw} rows -> "
          f"{len(out)} unique FUAs"
          + (f" ({dupes} duplicate rows resolved to the fullest-coverage row)"
             if dupes else ""))

    missing = [c for c in ("exDmg_mean", "dmg500_mean", "exInunD_a05_mean")
               if c not in out.columns]
    if missing:
        print(f"           note: band groups not yet present for {missing}; "
              f"the sections needing them will be skipped")
    if "wld_rgn" not in out.columns:
        out["wld_rgn"] = out["Cntry_name"].map(REGION_MAP)
        unmapped = sorted(out.loc[out["wld_rgn"].isna(), "Cntry_name"].unique())
        if unmapped:
            print(f"  [{dataset}] unmapped countries: {', '.join(unmapped)}")
    return out


def has(df: pd.DataFrame, *cols: str) -> bool:
    """True if every column is present, so a section can be skipped cleanly
    when its band group has not been exported yet."""
    return all(c in df.columns for c in cols)


def band_contributions(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Per-FUA contribution of each trapezoid band, reconstructed from per-RP means."""
    rows = {}
    for rare, freq, dp in BANDS:
        col = (df[f"{prefix}{rare}_mean"] + df[f"{prefix}{freq}_mean"]) * dp / 2
        rows[f"{freq}-{rare}yr"] = col
    return pd.DataFrame(rows)


def report_integration(df: pd.DataFrame, prefix: str, label: str) -> None:
    print(f"\n  {label}")
    contrib = band_contributions(df, prefix)
    total = contrib.sum(axis=1)
    ok = total > 0
    shares = contrib[ok].div(total[ok], axis=0) * 100
    for col in contrib.columns:
        print(f"    band {col:>12s}: median share of AED = {shares[col].median():5.1f}%"
              f"   mean = {shares[col].mean():5.1f}%")

    # Rare tail actually omitted by the published unprotected metrics.
    tail = df[f"{prefix}500_mean"] * P_MIN_MAPPED
    rel = (tail[ok] / total[ok]) * 100
    print(f"    omitted rare tail (p < {P_MIN_MAPPED}):"
          f" median = {rel.median():.2f}% of AED, P90 = {rel.quantile(0.9):.2f}%,"
          f" max = {rel.max():.2f}%")
    print(f"      absolute size: median = {tail[ok].median()*100:.4f} pp"
          f" (analytic upper bound is 0.2 pp, since damage <= 1)")

    # Frequent range omitted below the 10-yr map (p > 0.1).
    #
    # No data-driven bracket is possible here: the JRC/GloFAS maps provide no
    # inundation extent below the 10-yr event, so any "upper bound" would be an
    # invention rather than a measurement. (An earlier version of this script
    # extrapolated damage linearly to a 2-yr event and reported a figure near
    # 200% of AED; that number is an artefact of assuming the floodplain stays
    # fully inundated as discharge falls, and is not reported.)
    #
    # What can be said from the data is how strongly AED depends on the most
    # frequent mapped band, which indicates how consequential the truncation is.
    most_frequent = shares[contrib.columns[-1]]
    print(f"    omitted frequent range (p > {P_MAX_MAPPED}): assumed zero"
          f" (no hazard map exists below the 10-yr event).")
    print(f"      consequence indicator: the 10-20yr band alone contributes a median"
          f" {most_frequent.median():.1f}% of AED, so AED is dominated by frequent"
          f" events and this truncation biases unprotected estimates downward.")


def residual_by_standard(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """
    Residual AED for each candidate protection standard.

    A standard of T years intercepts every event more frequent than 1/T, so the
    residual is the trapezoid sum over the bands rarer than 1/T, plus the
    rare-event tail. Reported for the six mapped return periods, which is the
    full set of standards the hazard maps can resolve.

    The tail is included at every standard, "no protection" included, so the
    curve is monotone decreasing and usable directly as a benefit stream.
    (The published code adds the tail only to the protected metrics; that
    asymmetry is what section 2 quantifies.)
    """
    out = {"eFUA_ID": df["eFUA_ID"], "eFUA_name": df["eFUA_name"]}
    tail = df[f"{prefix}500_mean"] * P_MIN_MAPPED

    # n_bands surviving, counting from the rarest, for each standard.
    for standard, n_bands in [("no protection", 5), ("10yr", 5), ("20yr", 4),
                              ("50yr", 3), ("100yr", 2), ("200yr", 1),
                              ("500yr", 0)]:
        total = tail.copy()
        for rare, freq, dp in BANDS[:n_bands]:
            total = total + (df[f"{prefix}{rare}_mean"] +
                             df[f"{prefix}{freq}_mean"]) * dp / 2
        out[f"residual_{standard.replace(' ', '_')}"] = total
    return pd.DataFrame(out)


def main() -> None:
    if not DIAG.exists():
        print(f"Expected Earth Engine exports in {DIAG}")
        print("Run the gee/STAGE1*/STAGE2* diagnostics exports first.")
        sys.exit(1)

    data = {ds: load(ds) for ds in DATASETS}
    data = {k: v for k, v in data.items() if not v.empty}
    if not data:
        print("No diagnostic exports found.")
        sys.exit(1)

    print("=" * 78)
    print("A3  Integration diagnostics")
    print("=" * 78)
    for ds, df in data.items():
        print(f"  {ds:8s} FUAs = {len(df)}")

    # ---- 1. Where the AED comes from, and what the truncations cost ---------
    print("\n" + "-" * 78)
    print("1. Trapezoid band contributions and truncated ranges (R4 Comment 2)")
    print("-" * 78)
    ref = data.get("JRC", next(iter(data.values())))
    if has(ref, "dmg500_mean", "dmg10_mean"):
        report_integration(ref, "dmg", "FD-AED (depth-damage)")
        report_integration(ref, "inun", "IR-AED (inundation ratio)")
    else:
        print("  skipped: needs the 'perRP' band group (dmg10..dmg500,"
              " inun10..inun500)")

    # ---- 2. Tail harmonisation ---------------------------------------------
    print("\n" + "-" * 78)
    print("2. Harmonising the rare tail between protected and unprotected metrics")
    print("-" * 78)
    for ds, df in data.items():
        if not has(df, "exDmg_tail_mean", "exDmg_pros_mean"):
            print(f"  {ds:8s} skipped: needs the 'core' band group")
            continue
        published_inconsistent = (df["exDmg_pros_mean"] > df["exDmg_mean"]).sum()
        harmonised_inconsistent = (df["exDmg_pros_mean"] > df["exDmg_tail_mean"]).sum()
        shift = (df["exDmg_tail_mean"] / df["exDmg_mean"] - 1) * 100
        print(f"  {ds:8s} FUAs with protected > unprotected FD-AED:"
              f" published = {published_inconsistent}, harmonised = {harmonised_inconsistent}")
        print(f"           adding the tail raises unprotected FD-AED by a median"
              f" {shift.median():.2f}% (P90 = {shift.quantile(0.9):.2f}%)")

    # ---- 3. Protection rounded up vs down ----------------------------------
    print("\n" + "-" * 78)
    print("3. Protection standards snapped up vs down to a mapped return period")
    print("-" * 78)
    for ds, df in data.items():
        if not has(df, "exDmg_pros_mean", "exDmg_prosDn_mean"):
            print(f"  {ds:8s} skipped: needs the 'core' band group")
            continue
        up, dn = df["exDmg_pros_mean"], df["exDmg_prosDn_mean"]
        ok = dn > 0
        diff = ((dn[ok] - up[ok]) / dn[ok]) * 100
        print(f"  {ds:8s} rounding down raises residual FD-AED by a median"
              f" {diff.median():.1f}% (IQR {diff.quantile(.25):.1f}-{diff.quantile(.75):.1f}%)")
        print(f"           global mean residual FD-AED: round-up = {up.mean()*100:.3f}%,"
              f" round-down = {dn.mean()*100:.3f}%")

    # ---- 4. alpha sensitivity of the linear inundation ratio ---------------
    print("\n" + "-" * 78)
    print("4. Sensitivity to the linear depth-to-height assumption (R3 Comment 3)")
    print("-" * 78)
    for ds, df in data.items():
        if not has(df, "exInunD_a05_mean", "exInunD_a20_mean", "exInunD_mean"):
            print(f"  {ds:8s} skipped: needs the 'alpha' and 'core' band groups")
            continue
        a05, a10, a20 = df["exInunD_a05_mean"], df["exInunD_mean"], df["exInunD_a20_mean"]
        ok = np.isfinite(a05) & np.isfinite(a10) & np.isfinite(a20) & (a10 > 0)
        print(f"  {ds:8s} global mean IR-AED:"
              f" alpha=0.5 -> {a05[ok].mean()*100:.2f}%,"
              f" alpha=1 -> {a10[ok].mean()*100:.2f}%,"
              f" alpha=2 -> {a20[ok].mean()*100:.2f}%")
        r05 = stats.spearmanr(a10[ok], a05[ok]).statistic
        r20 = stats.spearmanr(a10[ok], a20[ok]).statistic
        print(f"           FUA rank correlation with the linear case:"
              f" alpha=0.5 rho = {r05:.4f}, alpha=2 rho = {r20:.4f}")
        if "wld_rgn" in df.columns:
            reg = df[ok].groupby("wld_rgn")[
                ["exInunD_a05_mean", "exInunD_mean", "exInunD_a20_mean"]].mean()
            share = reg.div(reg.sum(axis=0), axis=1) * 100
            share.columns = ["alpha=0.5", "alpha=1", "alpha=2"]
            print("\n           Regional share of global IR-AED (%):")
            print(share.round(2).to_string().replace("\n", "\n           "))

    # ---- 5. Three-dataset height sensitivity, WSF3D fix applied ------------
    print("\n" + "-" * 78)
    print("5. Building-height dataset sensitivity, recomputed (R4 Comment 5)")
    print("-" * 78)
    if len(data) == 3:
        cols = ["eFUA_ID", "eFUA_name", "height_mean", "exDmg_mean", "exInunD_mean"]
        merged = data["JRC"][cols].rename(
            columns={c: c + "_jrc" for c in ("height_mean", "exDmg_mean", "exInunD_mean")})
        for ds, suf in (("WSF3D", "_wsf3d"), ("GBH2020", "_gbh")):
            right = data[ds][["eFUA_ID", "height_mean", "exDmg_mean", "exInunD_mean"]]
            right = right.rename(columns=lambda c: c + suf if c != "eFUA_ID" else c)
            merged = merged.merge(right, on="eFUA_ID", how="inner")

        ir_cols = ["exInunD_mean_jrc", "exInunD_mean_wsf3d", "exInunD_mean_gbh"]
        h_cols = ["height_mean_jrc", "height_mean_wsf3d", "height_mean_gbh"]
        clean = merged.dropna(subset=ir_cols + h_cols)
        clean = clean[clean[ir_cols].sum(axis=1) > 0]

        h_means = np.array([clean[c].mean() for c in h_cols])
        ir_means = np.array([clean[c].mean() for c in ir_cols])
        print(f"  n FUAs = {len(clean)}")
        print(f"  height (m)  JRC {h_means[0]:.2f}  WSF3D {h_means[1]:.2f}"
              f"  GBH2020 {h_means[2]:.2f}   CV = {h_means.std(ddof=0)/h_means.mean()*100:.1f}%")
        print(f"  IR-AED (%)  JRC {ir_means[0]*100:.2f}  WSF3D {ir_means[1]*100:.2f}"
              f"  GBH2020 {ir_means[2]*100:.2f}   CV = {ir_means.std(ddof=0)/ir_means.mean()*100:.1f}%")

        vals = clean[ir_cols].to_numpy()
        per_fua = vals.std(axis=1, ddof=0) / vals.mean(axis=1) * 100
        print(f"  per-FUA CV of IR-AED: median = {np.median(per_fua):.1f}%,"
              f" IQR = {np.percentile(per_fua,25):.1f}-{np.percentile(per_fua,75):.1f}%")
        for a, b in [("jrc", "wsf3d"), ("jrc", "gbh"), ("wsf3d", "gbh")]:
            rho = stats.spearmanr(clean[f"exInunD_mean_{a}"],
                                  clean[f"exInunD_mean_{b}"]).statistic
            print(f"    {a:6s} vs {b:6s}  Spearman rho = {rho:.3f}")
        clean.to_csv(paths.out("a3_height_sensitivity_recomputed.csv"), index=False)
    else:
        print("  Needs all three height datasets; found: " + ", ".join(data))

    # ---- 5b. Effect of putting FD-AED on the built-up domain --------------
    print("\n" + "-" * 78)
    print("5b. FD-AED on the built-up floodplain vs the full floodplain")
    print("-" * 78)
    print("   exDmg   = FD-AED over pixels carrying a building height (built-up),")
    print("             the domain IR-AED has always used.")
    print("   exDmgFP = FD-AED over the whole modelled floodplain, which is what")
    print("             the published analysis reported.")
    for ds, df in data.items():
        if not has(df, "exDmg_mean", "exDmgFP_mean"):
            print(f"  {ds:8s} skipped: needs exDmgFP (re-run Stage 1 revision 2)")
            continue
        ok = (df["exDmgFP_mean"] > 0) & np.isfinite(df["exDmg_mean"])
        ratio = df.loc[ok, "exDmg_mean"] / df.loc[ok, "exDmgFP_mean"]
        print(f"  {ds:8s} n = {int(ok.sum())} FUAs")
        print(f"           built-up / full-floodplain FD-AED:"
              f" median {ratio.median():.3f}"
              f"  IQR {ratio.quantile(.25):.3f}-{ratio.quantile(.75):.3f}")
        print(f"           global mean FD-AED: built-up"
              f" {df.loc[ok,'exDmg_mean'].mean()*100:.2f}%,"
              f" full floodplain {df.loc[ok,'exDmgFP_mean'].mean()*100:.2f}%")

        # The paper's mechanism, now computed like-for-like.
        if has(df, "exInunD_mean"):
            ok2 = ok & (df["exInunD_mean"] > 0) & (df["exDmg_mean"] > 0)
            lr = df.loc[ok2, "exInunD_mean"] / df.loc[ok2, "exDmg_mean"]
            old = df.loc[ok2, "exInunD_mean"] / df.loc[ok2, "exDmgFP_mean"]
            print(f"           IR-AED / FD-AED, like-for-like : median {lr.median():.3f}")
            print(f"           IR-AED / FD-AED, as published  : median {old.median():.3f}")
            if "wld_rgn" in df.columns:
                g = df[ok2].groupby("wld_rgn").apply(
                    lambda x: pd.Series({
                        "n": len(x),
                        "like_for_like": (x.exInunD_mean / x.exDmg_mean).mean(),
                        "as_published": (x.exInunD_mean / x.exDmgFP_mean).mean(),
                        "mean_height_m": x.height_mean.mean()}),
                    include_groups=False)
                print("\n           IR/FD ratio by region (>1 = height raises the estimate):")
                print(g.sort_values("mean_height_m").round(3).to_string()
                      .replace("\n", "\n           "))

    # ---- 6. Residual loss as a function of the protection standard ---------
    # The per-return-period export makes this possible: residual AED under a
    # standard of T years is the trapezoid sum restricted to p < 1/T, plus the
    # tail. That curve is the marginal-benefit stream a cost-benefit appraisal
    # needs (R3 Comment 4), and it can now be produced for any city.
    print("\n" + "-" * 78)
    print("6. Residual FD-AED vs protection standard (R3 Comment 4)")
    print("-" * 78)
    ref = data.get("JRC", next(iter(data.values())))
    if has(ref, "dmg500_mean", "dmg10_mean"):
        curve = residual_by_standard(ref, "dmg")
        cities = ["Wuhan", "Bangkok", "Dhaka", "Ho Chi Minh City"]
        show = curve[curve["eFUA_name"].isin(cities)]
        if not show.empty:
            print(show.set_index("eFUA_name").round(4).to_string())
        curve.to_csv(paths.out("a3_residual_vs_standard_2026-08.csv"), index=False)
        print("\n  Wrote a3_residual_vs_standard.csv (all FUAs)")
    else:
        print("  skipped: needs the 'perRP' band group")

    for ds, df in data.items():
        df.to_csv(paths.out(f"a3_diag_{ds}_2026-08.csv"), index=False)
    print("\nWrote a3_diag_*.csv")


if __name__ == "__main__":
    main()
