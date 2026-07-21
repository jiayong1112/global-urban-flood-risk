// NEW (Jul 2026 revision): export total GDP per FUA.
// Denominator for the GDP-normalized losses requested by Reviewer 1:
//   normalized loss (% of GDP) = sum(AED x GDP) / sum(GDP)
// The numerator already exists in the *_GDP_fua_2026-1-8 exports
// (inAbove_floodRisk_fuaExport_GDP_Jan2026). This script exports the missing
// denominator using the same GDP layer (Kummu adm2 GDP per capita PPP 2022 x GHS-POP 2020).
// Country and region denominators are aggregated from these FUA rows in Python
// (each row carries country_na and wld_rgn), matching how the manuscript
// aggregates FUA metrics to countries and regions.
//
// Run in the Code Editor, then download the CSV from Drive folder
// csv_fua_totalGDP_2026-7 into the project data/ folder.

var fua = ee.FeatureCollection("users/Jiayong_Liang/Research_projects/FUA2015_100Mpop");

var gdp_adm2 = ee.Image("projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022");
var pop2020 = ee.Image('JRC/GHSL/P2023A/GHS_POP/2020');
var totalGDP = gdp_adm2.select('PPP_2022').multiply(pop2020).rename('totalGDP');

var stats = totalGDP.reduceRegions({
  collection: fua,
  reducer: ee.Reducer.sum(),
  scale: 100
})
.map(function (ft) { return ft.setGeometry(null); })
.map(function (ft) {
  return ft.set('sum', ee.Algorithms.If(ft.get('sum'), ft.get('sum'), 0));
});

Export.table.toDrive({
  collection: stats,
  folder: 'csv_fua_totalGDP_2026-7',
  description: 'fua_totalGDP_2026-7',
  fileFormat: 'CSV'
});

// If the global export exceeds memory limits, split it by region with the same
// getRegionCol()/filterBounds pattern used in inAbove_floodRisk_fuaExport_GDP_Jan2026.
