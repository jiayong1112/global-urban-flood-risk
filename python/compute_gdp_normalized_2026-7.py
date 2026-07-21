"""
GDP-normalized flood losses (Jul 2026 revision, Reviewer 1 comment 1).

normalized loss (% of GDP) = sum(AED x pixelGDP) / sum(pixelGDP)
  numerator:   csv_fua_2026-1-17/JRC_[Region]_GDP.csv  (exDmg_sum etc., USD)
  denominator: data/fua_totalGDP_2026-7.csv            (total GDP per FUA, USD)

Outputs:
  data/gdp_normalized_region_2026-7.csv   (11 world regions)
  data/gdp_normalized_country_2026-7.csv  (countries)
Also prints a verification block comparing GDP-weighted totals/shares
against the numbers reported in the manuscript (Fig 1b: East Asia $296B/67%,
SE Asia $31B, Europe $27B, S Asia $24B).
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SRC_1_17 = BASE / "2026-1_inAbove_Flood_SR" / "Scientific Reports" / "2026-1 submission" / "csv_fua_2026-1-17"
TOTALGDP_CSV = BASE / "data" / "fua_totalGDP_2026-7.csv"
OUT_DIR = BASE / "data"

CONTINENT_FILES = ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]
METRICS = ["exDmg_sum", "exDmg_pros_sum", "exInunD_sum", "exInunD_pros_sum"]

# Country -> world region mapping, copied from combine_fua_data.py (Jan 2026)
# so regions match the published figures; extended where FUAs were unmapped.
REGION_MAP = {
    'Algeria': 'Africa', 'Angola': 'Africa', 'Benin': 'Africa', 'BurkinaFaso': 'Africa',
    'Cameroon': 'Africa', 'Chad': 'Africa', 'CotedIvoire': 'Africa', 'Egypt': 'Africa',
    'Ethiopia': 'Africa', 'Ghana': 'Africa', 'Kenya': 'Africa', 'Libya': 'Africa',
    'Mali': 'Africa', 'Morocco': 'Africa', 'Mozambique': 'Africa', 'Nigeria': 'Africa',
    'SouthAfrica': 'Africa', 'Tanzania': 'Africa', 'Tunisia': 'Africa', 'Uganda': 'Africa',
    'Zambia': 'Africa', 'Zimbabwe': 'Africa', 'Senegal': 'Africa', 'Congo(DRC)': 'Africa',
    'Sudan': 'Africa', 'Madagascar': 'Africa',
    'Austria': 'Europe', 'Belgium': 'Europe', 'Bulgaria': 'Europe', 'Croatia': 'Europe',
    'CzechRepublic': 'Europe', 'Denmark': 'Europe', 'Finland': 'Europe', 'France': 'Europe',
    'Germany': 'Europe', 'Greece': 'Europe', 'Hungary': 'Europe', 'Ireland': 'Europe',
    'Italy': 'Europe', 'Netherlands': 'Europe', 'Norway': 'Europe', 'Poland': 'Europe',
    'Portugal': 'Europe', 'Romania': 'Europe', 'Serbia': 'Europe', 'Slovakia': 'Europe',
    'Spain': 'Europe', 'Sweden': 'Europe', 'Switzerland': 'Europe', 'Ukraine': 'Europe',
    'UnitedKingdom': 'Europe', 'UnitedKingdom(Scotland)': 'Europe',
    'Canada': 'N America', 'UnitedStates': 'N America', 'Mexico': 'N America',
    'CostaRica': 'C America', 'DominicanRepublic': 'C America', 'ElSalvador': 'C America',
    'Guatemala': 'C America', 'Honduras': 'C America', 'Nicaragua': 'C America', 'Panama': 'C America',
    'Argentina': 'S America', 'Bolivia': 'S America', 'Brazil': 'S America',
    'Chile': 'S America', 'Colombia': 'S America', 'Ecuador': 'S America',
    'Paraguay': 'S America', 'Peru': 'S America', 'Uruguay': 'S America', 'Venezuela': 'S America',
    'China': 'E Asia', 'Japan': 'E Asia', 'NorthKorea': 'E Asia', 'SouthKorea': 'E Asia',
    'Taiwan': 'E Asia', 'Mongolia': 'E Asia',
    'Cambodia': 'SE Asia', 'Indonesia': 'SE Asia', 'Laos': 'SE Asia', 'Malaysia': 'SE Asia',
    'Myanmar': 'SE Asia', 'Philippines': 'SE Asia', 'Singapore': 'SE Asia', 'Thailand': 'SE Asia',
    'Vietnam': 'SE Asia', 'Brunei': 'SE Asia',
    'Afghanistan': 'S Asia', 'Bangladesh': 'S Asia', 'India': 'S Asia',
    'Nepal': 'S Asia', 'Pakistan': 'S Asia', 'SriLanka': 'S Asia',
    'Iran': 'SW Asia', 'Iraq': 'SW Asia', 'Israel': 'SW Asia', 'Jordan': 'SW Asia',
    'Lebanon': 'SW Asia', 'Oman': 'SW Asia', 'SaudiArabia': 'SW Asia', 'Syria': 'SW Asia',
    'Turkey': 'SW Asia', 'UnitedArabEmirates': 'SW Asia', 'Yemen': 'SW Asia',
    'Kuwait': 'SW Asia', 'Qatar': 'SW Asia', 'Bahrain': 'SW Asia',
    'Kazakhstan': 'C Asia', 'Kyrgyzstan': 'C Asia', 'Russia': 'C Asia',
    'Tajikistan': 'C Asia', 'Turkmenistan': 'C Asia', 'Uzbekistan': 'C Asia',
    'Australia': 'Oceania', 'NewZealand': 'Oceania', 'PapuaNewGuinea': 'Oceania',
    'Fiji': 'Oceania',
}


def load_numerator():
    frames = []
    for c in CONTINENT_FILES:
        f = SRC_1_17 / f"JRC_{c}_GDP.csv"
        df = pd.read_csv(f)
        df["src_file"] = c
        frames.append(df)
    gdp = pd.concat(frames, ignore_index=True)
    dupes = gdp[gdp.duplicated("eFUA_ID", keep=False)]
    if len(dupes):
        print(f"[warn] {dupes['eFUA_ID'].nunique()} duplicated eFUA_IDs across files; keeping first")
        print(dupes[["eFUA_ID", "eFUA_name", "Cntry_name", "src_file"]].sort_values("eFUA_ID").to_string())
        gdp = gdp.drop_duplicates("eFUA_ID", keep="first")
    return gdp


def main():
    gdp = load_numerator()
    print(f"numerator FUAs: {len(gdp)}")

    tot = pd.read_csv(TOTALGDP_CSV)[["eFUA_ID", "eFUA_name", "Cntry_name", "sum"]]
    tot = tot.rename(columns={"sum": "totalGDP"}).drop_duplicates("eFUA_ID", keep="first")
    print(f"denominator FUAs: {len(tot)}")

    m = gdp.merge(tot[["eFUA_ID", "totalGDP"]], on="eFUA_ID", how="left", validate="1:1")
    missing = m[m["totalGDP"].isna() | (m["totalGDP"] <= 0)]
    if len(missing):
        print(f"[warn] {len(missing)} FUAs without positive totalGDP (dropped from normalization):")
        print(missing[["eFUA_ID", "eFUA_name", "Cntry_name"]].to_string())
    m = m[m["totalGDP"] > 0].copy()

    m["wld_rgn"] = m["Cntry_name"].map(REGION_MAP)
    unmapped = m[m["wld_rgn"].isna()]
    if len(unmapped):
        print(f"[warn] unmapped countries ({unmapped['Cntry_name'].nunique()}): "
              f"{sorted(unmapped['Cntry_name'].unique())} "
              f"({len(unmapped)} FUAs) — excluded from region table, kept in country table")

    # ---------- region level ----------
    reg = m.dropna(subset=["wld_rgn"]).groupby("wld_rgn")[METRICS + ["totalGDP"]].sum()
    reg["n_fuas"] = m.dropna(subset=["wld_rgn"]).groupby("wld_rgn").size()
    for met in METRICS:
        reg[met.replace("_sum", "_bnUSD")] = reg[met] / 1e9
        reg[met.replace("_sum", "_share_pct")] = 100 * reg[met] / reg[met].sum()
        reg[met.replace("_sum", "_pctGDP")] = 100 * reg[met] / reg["totalGDP"]
    reg["totalGDP_bnUSD"] = reg["totalGDP"] / 1e9
    reg = reg.sort_values("exDmg_sum", ascending=False)

    out_cols = (["n_fuas", "totalGDP_bnUSD"]
                + [met.replace("_sum", s) for met in METRICS for s in ("_bnUSD", "_share_pct", "_pctGDP")])
    reg_out = reg[out_cols].round(4)
    reg_path = OUT_DIR / "gdp_normalized_region_2026-7.csv"
    reg_out.to_csv(reg_path)
    print(f"\nwrote {reg_path}")

    # ---------- country level ----------
    cty = m.groupby(["Cntry_name", "wld_rgn"], dropna=False)[METRICS + ["totalGDP"]].sum().reset_index()
    cty["n_fuas"] = m.groupby(["Cntry_name", "wld_rgn"], dropna=False).size().values
    for met in METRICS:
        cty[met.replace("_sum", "_pctGDP")] = 100 * cty[met] / cty["totalGDP"]
    cty_path = OUT_DIR / "gdp_normalized_country_2026-7.csv"
    cty.round(6).to_csv(cty_path, index=False)
    print(f"wrote {cty_path}")

    # ---------- verification against manuscript Fig 1b ----------
    pd.set_option("display.width", 200)
    print("\n=== GDP-weighted FD-AED by region (verify vs manuscript: E Asia $296B/67%, SE Asia $31B, Europe $27B, S Asia $24B) ===")
    print(reg[["exDmg_bnUSD", "exDmg_share_pct"]].round(2).to_string())

    print("\n=== Normalized: annual expected loss as % of regional GDP ===")
    print(reg[["totalGDP_bnUSD", "exDmg_pctGDP", "exInunD_pctGDP", "exDmg_pros_pctGDP", "exInunD_pros_pctGDP"]]
          .round(3).to_string())

    print("\n=== Manuscript share checks (GDP-weighted) ===")
    def share(colsum, regions):
        return 100 * reg.loc[reg.index.isin(regions), colsum].sum() / reg[colsum].sum()
    well = ["Europe", "N America", "Oceania", "E Asia"]
    poor3 = ["S Asia", "SE Asia", "Africa"]
    print(f"Africa share FD-AED (ms 2.8%):            {share('exDmg_sum', ['Africa']):.1f}%")
    print(f"Africa share IR-AED (ms 4.2%):            {share('exInunD_sum', ['Africa']):.1f}%")
    print(f"Europe share FD-AED (ms 6.1%):            {share('exDmg_sum', ['Europe']):.1f}%")
    print(f"Europe share IR-AED (ms 8.1%):            {share('exInunD_sum', ['Europe']):.1f}%")
    print(f"S Asia share FD-AED (ms 5.5%):            {share('exDmg_sum', ['S Asia']):.1f}%")
    print(f"S Asia share IR-AED (ms 6.8%):            {share('exInunD_sum', ['S Asia']):.1f}%")
    print(f"E Asia share FD-AED (ms 67.0%):           {share('exDmg_sum', ['E Asia']):.1f}%")
    print(f"E Asia share IR-AED (ms 61.4%):           {share('exInunD_sum', ['E Asia']):.1f}%")
    print(f"Well-protected 4 pre-prot FD (ms 78%):    {share('exDmg_sum', well):.1f}%")
    print(f"Well-protected 4 post-prot FD (ms 57%):   {share('exDmg_pros_sum', well):.1f}%")
    print(f"SAsia+SEAsia+Africa pre-prot FD (ms 15%): {share('exDmg_sum', poor3):.1f}%")
    print(f"SAsia+SEAsia+Africa post-prot FD (ms 35%): {share('exDmg_pros_sum', poor3):.1f}%")


if __name__ == "__main__":
    main()
