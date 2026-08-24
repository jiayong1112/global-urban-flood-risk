# Height-Aware and Protection-Informed Global Urban Flood Assessment

Code and summary data for:

> Liang, J., Hilaly, I., Gao, X., Guan, C., Li, Y., Huang, K. *Height-Aware and
> Protection-Informed Flood Assessment Shifts Global Urban Risk Distribution.*
> Scientific Reports (under review).

This repository contains the Google Earth Engine (GEE) scripts that compute the
flood-risk metrics, the Python scripts that aggregate the exported tables and
generate the figures, and the summary tables behind every figure and
supplementary table. It is deposited to satisfy the Code Availability
requirement and to enable reproduction of the reported results.

## Metrics

- **FD-AED** — Flood-Depth-based Annual Expected Damage
- **IR-AED** — Inundation-Ratio-based Annual Expected Damage. This is a
  height-normalized index of potential structural exposure (flood depth /
  building height), not a calibrated damage estimate; "Annual Expected Damage"
  is retained in the acronym for symmetry with FD-AED.
- **FD-AED-P, IR-AED-P** — the above after applying FLOPROS flood-protection standards
- GDP-weighted (absolute US$) and GDP-normalized (% of GDP) variants of each

## Version 2026-08

The current pixel-level module is `gee/module_floodRisk_inAbove_2026-08.js`; the
current per-FUA export is `gee/fuaExport_2026-08.js`. They supersede the
`*_Jan2026.js` files, which are retained for provenance. Four changes:

1. **The rare-event tail is integrated over the same probability range for the
   protected and unprotected metrics.** The rectangular term D(d500) × p was
   previously added only to the two rarest protection bins and to neither the
   other bins nor the unprotected metrics, so the two families were integrated
   over slightly different ranges and a protected value could come out
   marginally above the unprotected one. Every metric now carries the tail
   (p = 1/500; 1/1000 for the ≥ 500-yr bin), which bounds the protected value
   above by the unprotected value at every pixel.
2. **Pixels with no FLOPROS record are masked out**, not assumed unprotected.
   The same mask is applied to a matching pair of unprotected bands
   (`exDmg_cmp`, `exInunD_cmp`) so the compared metrics share a domain and the
   bound in (1) survives spatial averaging.
3. **Building height is exported on two domains**: `height` (FUA-wide, the
   statistic quoted in the text) and `height_fp` (the built-up floodplain, the
   pixels the inundation ratio actually uses).
4. **The country-to-region mapping is now a single shared module,**
   `python/region_map.py`. It was previously inlined separately in
   `combine_fua_data.py`, `compute_gdp_normalized_2026-7.py` and the
   integration-diagnostics script. Those copies disagreed on **Russia**, which
   two of them placed in Central Asia while Table S2 and the reported results
   place it in Europe. Russia contributes 15 FUAs to the main assembled series
   and 10 to the diagnostics sample, so the disagreement changed every regional
   row of Supplementary Tables S5 and S7. All scripts now import the one map;
   `python region_map.py` prints its size and the corrections it applies.

`fuaExport_2026-08.js` also selects FUAs by country name rather than by a
dissolved LSIB region geometry. The dissolved-geometry selection returned only
6 of Mexico's 14 FUAs in the January export; the `Mexico` batch fills that gap.

### Revision diagnostics

The `STAGE*_diagnostics_*.js` exports and the `python/a1`–`a6` scripts were
added for the 2026-08 revision. They produce the per-return-period diagnostics
that the supplementary tables report:

| Script | What it answers |
|---|---|
| `a1_height_dataset_sensitivity.py` | IR-AED under JRC, WSF3D and GBH2020 heights, with the WSF3D decimetre-to-metre correction applied consistently |
| `a2_decision_support_numbers.py` | avoided expected annual loss per FUA, the benefit stream an appraisal would use |
| `a3_integration_diagnostics.py` | contribution of each return-period band, size of the truncated rare tail, protection rounded up vs. down, α-sensitivity of the inundation ratio, and FD-AED on the built-up vs. full floodplain |
| `a4_rebuild_2026-08.py`, `a5_assemble_2026-08.py` | reassemble the FUA and country tables from the August exports |
| `a6_results_2026-08.py` | regenerates every number quoted in the Results |

## Pipeline

1. **Pixel-level risk (GEE).** `gee/module_floodRisk_inAbove_2026-08.js` is the core
   module: it combines JRC CEMS-GLOFAS flood hazard (return periods 10-500 yr),
   building height (JRC GHSL primary; WSF3D and GBH2020 for sensitivity), regional
   Huizinga (2017) depth-damage curves, and FLOPROS protection standards, then
   integrates over annual exceedance probability to produce FD-AED, IR-AED, and their
   protected versions per ~100 m pixel.
2. **Aggregation and export (GEE).** The `*Export_*` scripts reduce the pixel image to
   functional urban areas (FUA) and countries, exporting CSVs:
   - `fuaExport_2026-08.js` — normalized metrics, current version
   - `fuaExport_GDP_2026-08.js` — GDP-weighted (US$), current version
   - `fuaExport_Jan2026.js`, `cntyExport_Jan2026.js` — normalized metrics (superseded)
   - `fuaExport_GDP_Jan2026.js`, `cntyExport_GDP_Jan2026.js` — GDP-weighted (superseded)
   - `inAbove_floodRisk_totalGDP_fuaExport_Jul2026.js` — total GDP per FUA (denominator
     for GDP normalization)
   - `mapExport_Jan2026.js`, `fig4_export_Jul2026.js` — raster exports for the maps
   - `STAGE1*_diagnostics_toAsset_2026-08.js`, `STAGE2*_diagnostics_fuaExport_2026-08.js`
     — per-return-period diagnostics behind Tables S3-S7
3. **Country aggregation (Python).** `python/combine_fua_data.py` aggregates the FUA
   tables to countries (mean for normalized metrics, sum for GDP), using the shared
   mapping in `python/region_map.py`.
4. **GDP normalization (Python).** `python/compute_gdp_normalized_2026-08.py` divides the
   GDP-weighted losses by total GDP to produce loss as a percentage of GDP
   (`data/gdp_normalized_region_2026-08.csv`, `data/gdp_normalized_country_2026-08.csv`).
5. **Figures (Python).** Each script reads the summary tables and writes one figure:
   | Script | Figure |
   |---|---|
   | `fig1_regional_metrics_2026-08.py` | Fig 1: regional shares, GDP-weighted, and % of GDP |
   | `fig2_tertile_maps_2026-08.py` | Fig 2: country FD-AED vs IR-AED tertile maps |
   | `fig3_boxplots_2026-08.py` | Fig 3: country- and city-scale indicator distributions |
   | `fig4_city_maps_2026-7.py` | Fig 4: within-city composite maps (Sentinel-2 basemap) |
   | `fig1_arrows_2026-08.py` | Fig 1 alternative rendering |
   | `a1_height_dataset_sensitivity.py` | building-height sensitivity analysis |

## What backs each figure and table

Every deposited table is an output of the scripts above, at the state used for the
manuscript. The `*_2026-7.csv` tables are the superseded July versions.

| Manuscript item | Deposited file |
|---|---|
| Figure 1 (a) | `data/fig1_panelA_shares_2026-08.csv` |
| Figure 1 (b), (c) | `data/gdp_normalized_region_2026-08.csv` |
| Figures 2 and 3, and the Results values | `data/a5_country_2026-08.csv`, `data/a5_fua_2026-08.csv` |
| Country-level summary | `data/country_table_2026-08.csv`, `data/gdp_normalized_country_2026-08.csv` |
| Tables S3, S5, S7 (band contributions, α-sensitivity, IR/FD by region) | `data/a3_diag_JRC_2026-08.csv` |
| Table S6 (residual FD-AED by candidate standard, all FUAs) | `data/a3_residual_vs_standard_2026-08.csv` |
| Building-height sensitivity (Discussion) | `data/a1_height_sensitivity_summary_2026-08.csv`, `data/a1_height_sensitivity_per_fua_2026-08.csv` |
| Avoided-loss illustration (Discussion) | `data/a2_decision_support_2026-08.csv` |
| GDP denominator for the normalized metrics | `data/fua_totalGDP_2026-7.csv` |

Sample sizes differ between tables because the available *n* varies by
indicator: the assembled series holds 127 countries and 665 FUAs, of which 120
countries and 642 FUAs carry valid positive values for all four indicators,
while the integration diagnostics cover the 647 FUAs with complete diagnostic
outputs.

## Data sources (public)

JRC CEMS-GLOFAS river flood hazard v2.1; JRC GHSL built height 2023A and GHS-POP 2020;
WSF3D (DLR); GBH2020 (Ma et al. 2024); FLOPROS (Scussolini et al. 2016);
Huizinga et al. (2017) depth-damage functions; Kummu et al. (2025) gridded GDP per
capita PPP; GHS-FUA and USDOS LSIB boundaries; Copernicus Sentinel-2 surface
reflectance (Fig 4 basemap).

## Repository layout

Every script resolves its paths relative to the repository, so a fresh clone
works with no editing. Three directories:

| Directory | Tracked | Contents |
|---|---|---|
| `data/` | yes | The summary tables used for the manuscript |
| `exports/` | no | Earth Engine exports you generate; see `exports/README.md` |
| `output/` | no | Everything the scripts write: figures and regenerated tables |

Set `GUFR_EXPORTS` if the exports already live elsewhere on your machine, and
`GUFR_OUTPUT` to write results somewhere other than `output/`. Run
`python python/paths.py` to print every location and whether it is present.

Summary tables are read through a helper that prefers a copy you have just
regenerated in `output/` and falls back to the deposited copy in `data/`. So the
figure scripts draw the published figures from a bare clone, and redraw them
from your own numbers once you have re-run the analysis.

## Reproducing the figures

```bash
pip install pandas numpy scipy matplotlib geopandas rasterio pillow
```

**From a bare clone, with no Earth Engine access.** These read the deposited
tables in `data/`:

```bash
python python/region_map.py                  # print the shared mapping and its corrections
python python/a6_results_2026-08.py          # every number quoted in the Results
python python/fig1_regional_metrics_2026-08.py
python python/fig3_boxplots_2026-08.py
python python/fig2_tertile_maps_2026-08.py   # also needs the Natural Earth basemap
```

**Recomputing the tables from the Earth Engine exports.** Place the exports as
described in `exports/README.md`, then:

```bash
python python/a5_assemble_2026-08.py         # FUA and country tables
python python/a3_integration_diagnostics.py  # Tables S3-S7
python python/compute_gdp_normalized_2026-08.py
python python/a1_height_dataset_sensitivity.py
python python/a2_decision_support_numbers.py
python python/fig4_city_maps_2026-7.py       # needs the Fig 4 GeoTIFFs
```

Re-running `a5_assemble_2026-08.py` and `a3_integration_diagnostics.py` from the
deposited Earth Engine exports reproduces `data/a5_fua_2026-08.csv`,
`data/a5_country_2026-08.csv`, `data/a3_diag_JRC_2026-08.csv` and
`data/a3_residual_vs_standard_2026-08.csv` exactly, to zero numerical
difference.

The GEE scripts run in the Earth Engine Code Editor and are also available at:
https://code.earthengine.google.com/?scriptPath=users%2FJiayong_Liang%2Fpublic%3Aglobal_flood_risk

Interactive results: https://kangning-huang.github.io/3D-urban-flood-risk/

## Note on the building-height configuration

`module_floodRisk_inAbove_2026-08.js` selects the building-height dataset near the top
(JRC GHSL is the primary source used for the reported results; WSF3D and GBH2020 are
provided for the sensitivity analysis and are commented out by default). WSF3D V02
reports height in decimetres and is converted to metres at the point of use.

## License

Code is released under the MIT License (see LICENSE). Input datasets remain under their
respective providers' licenses.
