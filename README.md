# Height-Aware and Protection-Informed Global Urban Flood Assessment

Code and summary data for:

> Liang, J., Hilaly, I., Gao, X., Guan, C., Li, Y., Huang, K. *Height-Aware and
> Protection-Informed Flood Assessment Shifts Global Urban Risk Distribution.*
> Scientific Reports (under review).

This repository contains the Google Earth Engine (GEE) scripts that compute the
flood-risk metrics, the Python scripts that aggregate the exported tables and
generate the figures, and the summary tables behind the figures. It is deposited
to satisfy the Code Availability requirement and to enable reproduction of the
reported results.

## Metrics

- **FD-AED** — Flood-Depth-based Annual Expected Damage
- **IR-AED** — Inundation-Ratio-based Annual Expected Damage (flood depth / building height)
- **FD-AED-P, IR-AED-P** — the above after applying FLOPROS flood-protection standards
- GDP-weighted (absolute US$) and GDP-normalized (% of GDP) variants of each

## Pipeline

1. **Pixel-level risk (GEE).** `gee/module_floodRisk_inAbove_Jan2026.js` is the core
   module: it combines JRC CEMS-GLOFAS flood hazard (return periods 10-500 yr),
   building height (JRC GHSL primary; WSF3D and GBH2020 for sensitivity), regional
   Huizinga (2017) depth-damage curves, and FLOPROS protection standards, then
   integrates over annual exceedance probability to produce FD-AED, IR-AED, and their
   protected versions per ~100 m pixel.
2. **Aggregation and export (GEE).** The `*Export_*` scripts reduce the pixel image to
   functional urban areas (FUA) and countries, exporting CSVs:
   - `fuaExport_Jan2026.js`, `cntyExport_Jan2026.js` — normalized metrics
   - `fuaExport_GDP_Jan2026.js`, `cntyExport_GDP_Jan2026.js` — GDP-weighted (US$)
   - `totalGDP_fuaExport_Jul2026.js` — total GDP per FUA (denominator for GDP normalization)
   - `mapExport_Jan2026.js`, `fig4_export_Jul2026.js` — raster exports for the maps
3. **Country aggregation (Python).** `python/combine_fua_data.py` aggregates the FUA
   tables to 108 countries (mean for normalized metrics, sum for GDP).
4. **GDP normalization (Python).** `python/compute_gdp_normalized_2026-7.py` divides the
   GDP-weighted losses by total GDP to produce loss as a percentage of GDP
   (`data/gdp_normalized_region_2026-7.csv`, `data/gdp_normalized_country_2026-7.csv`).
5. **Figures (Python).** Each script reads the summary tables and writes one figure:
   | Script | Figure |
   |---|---|
   | `fig1_regional_metrics_2026-7.py` | Fig 1: regional shares, GDP-weighted, and % of GDP |
   | `fig2_tertile_maps_2026-7.py` | Fig 2: country FD-AED vs IR-AED tertile maps |
   | `fig3_boxplots_2026-7.py` | Fig 3: country- and city-scale metric distributions |
   | `fig4_city_maps_2026-7.py` | Fig 4: within-city composite maps (Sentinel-2 basemap) |
   | `compare_building_height_datasets_2026-1-17.py` | building-height sensitivity analysis |

## Data sources (public)

JRC CEMS-GLOFAS river flood hazard v2.1; JRC GHSL built height 2023A and GHS-POP 2020;
WSF3D (DLR); GBH2020 (Ma et al. 2024, Google/WRI); FLOPROS (Scussolini et al. 2016);
Huizinga et al. (2017) depth-damage functions; Kummu et al. (2018/2025) gridded GDP;
GHS-FUA and USDOS LSIB boundaries; Copernicus Sentinel-2 surface reflectance (Fig 4 basemap).

## Reproducing the figures

```bash
pip install pandas numpy matplotlib geopandas rasterio pillow
# place the GEE-exported CSVs where each script expects them (see script headers),
# then:
python python/compute_gdp_normalized_2026-7.py
python python/fig1_regional_metrics_2026-7.py
python python/fig2_tertile_maps_2026-7.py
python python/fig3_boxplots_2026-7.py
python python/fig4_city_maps_2026-7.py   # needs the Fig 4 GeoTIFFs from fig4_export_Jul2026.js
```

The GEE scripts run in the Earth Engine Code Editor and are also available at:
https://code.earthengine.google.com/?scriptPath=users%2FJiayong_Liang%2Fpublic%3Aglobal_flood_risk

Interactive results: https://kangning-huang.github.io/3D-urban-flood-risk/

## Note on the building-height configuration

`module_floodRisk_inAbove_Jan2026.js` selects the building-height dataset near the top
(JRC GHSL is the primary source used for the reported results; WSF3D and GBH2020 are
provided for the sensitivity analysis and are commented out by default).

## License

Code is released under the MIT License (see LICENSE). Input datasets remain under their
respective providers' licenses.
