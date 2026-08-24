# Earth Engine exports

The scripts in `python/` read their raw inputs from this directory. The files
are Earth Engine exports, too large to redistribute here, so this directory is
empty in a fresh clone and is ignored by git.

You do **not** need any of this to redraw the published figures: the summary
tables in `data/` are deposited, and `fig1_regional_metrics_2026-08.py`,
`fig3_boxplots_2026-08.py` and `a6_results_2026-08.py` run from a bare clone.
You need the exports only to recompute those tables from scratch.

Run the scripts in `gee/` in the Earth Engine Code Editor and place the
downloaded CSVs here:

| Subdirectory | Produced by | Used by |
|---|---|---|
| `csv_fua_2026-1-17/` | `fuaExport_Jan2026.js`, plus the WSF3D and GBH2020 height variants | `a1`, `a2`, `a5` (reproduction check), `country_table`, `compute_gdp_normalized_*` |
| `flood_fua_2026-08/` | `fuaExport_2026-08.js` | `a5_assemble_2026-08.py` |
| `flood_fua_GDP_2026-08/` | `fuaExport_GDP_2026-08.js` | `a2_decision_support_numbers.py` |
| `csv_fua_diag_2026-08/` | `STAGE1*_diagnostics_toAsset_2026-08.js`, then `STAGE2*_diagnostics_fuaExport_2026-08.js` | `a3_integration_diagnostics.py` |
| `fig4_tiffs_2026-7/` | `fig4_export_Jul2026.js` | `fig4_city_maps_2026-7.py` |

Two inputs are not Earth Engine exports:

- `ne_110m_admin_0_countries/` — the Natural Earth 1:110m admin-0 countries
  shapefile, the basemap for the Figure 2 tertile maps. Download it from
  naturalearthdata.com and unzip it here.
- `fua_world_countries_2026-1-8.csv` — the January country-level aggregate,
  used only by the superseded July figure scripts.

If these files already exist somewhere on your machine, leave this directory
empty and point `GUFR_EXPORTS` at the directory that holds them instead:

```bash
GUFR_EXPORTS=/path/to/my/exports python python/a5_assemble_2026-08.py
```

Run `python python/paths.py` to print every location and whether it is present.
