// =============================================================================
// calculate totla GDP around 2022 to use in other script
var gdp_adm2 = ee.Image("projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022");
var image2020 = ee.Image('JRC/GHSL/P2023A/GHS_POP/2020');

var totalGDP_2020 = gdp_adm2.select('PPP_2022').multiply(image2020);
// =============================================================================

var floodRisk_img = ee.Image("users/Jiayong_Liang/Research_projects/FloodRiskViewGlobal_Jan2026_bh-JRC")
                    .select(['exDmg', 'exDmg_pros', 'exInunD', 'exInunD_pros']).multiply(totalGDP_2020);

// var imageVisParam_3view = {"opacity":1,"bands":["exDep","exDmg","exInunD"],"min":0.005,"max":0.05,"gamma":1};
// Map.addLayer(floodRisk_img, imageVisParam_3view, 'flood_jan26 Flood Risk View composite');

// imgDamageRegion: Asia   NAmerica  Europe Africa CSAmerica Oceania
var imgDamageRegion = "NAmerica"

var LSIB_SIMPLE = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017');

function getRegionCol(expectedDamage) {
  var regionCol = LSIB_SIMPLE;
  
  switch (expectedDamage) {
    case 'NAmerica':
      regionCol = regionCol.filter(ee.Filter.eq('wld_rgn', 'North America'));
      break;
    case 'Asia':
      regionCol = regionCol.filter(ee.Filter.or(
        ee.Filter.eq('wld_rgn', 'E Asia'),
        ee.Filter.eq('wld_rgn', 'S Asia'),
        ee.Filter.eq('wld_rgn', 'SE Asia'),
        ee.Filter.eq('wld_rgn', 'SW Asia'),
        ee.Filter.eq('wld_rgn', 'N Asia'),
        ee.Filter.eq('wld_rgn', 'Central Asia')
      ));
      break;
    case 'Europe':
      regionCol = regionCol.filter(ee.Filter.eq('wld_rgn', 'Europe'));
      break;
    case 'Africa':
      regionCol = regionCol.filter(ee.Filter.eq('wld_rgn', 'Africa'));
      break;
    case 'CSAmerica':
      regionCol = regionCol.filter(ee.Filter.or(
        ee.Filter.eq('wld_rgn', 'South America'),
        ee.Filter.eq('wld_rgn', 'Central America')
      ));
      break;
    case 'Oceania':
      regionCol = regionCol.filter(ee.Filter.or(
        ee.Filter.eq('wld_rgn', 'Oceania'),
        ee.Filter.eq('wld_rgn', 'Australia')
      ));
      break;
  }
  
  return regionCol;
}

var regionCol = getRegionCol(imgDamageRegion);

Map.addLayer(regionCol, {color: 'blue'}, 'regionCol', false);
// print(regionCol)

var reducers = ee.Reducer.mean()
.combine({
  reducer2: ee.Reducer.stdDev(),
  sharedInputs: true
})
.combine({
  reducer2: ee.Reducer.count(),
  sharedInputs: true
})
.combine({
  reducer2: ee.Reducer.sum(),
  sharedInputs: true
})

var multiStats = floodRisk_img.reduceRegions({
  collection: regionCol,
  reducer: reducers,
  scale: 100,
})
.map(function(ft){
  return ft.setGeometry(null);
})
.map(function(ft){
  var propertyNames = [
    'abbreviati',
    'country_co',
    'country_na',
    'exDmg_count',
    'exDmg_mean',
    'exDmg_pros_count',
    'exDmg_pros_mean',
    'exDmg_pros_stdDev',
    'exDmg_pros_sum',
    'exDmg_stdDev',
    'exDmg_sum',
    'exInunD_count',
    'exInunD_mean',
    'exInunD_pros_count',
    'exInunD_pros_mean',
    'exInunD_pros_stdDev',
    'exInunD_pros_sum',
    'exInunD_stdDev',
    'exInunD_sum',
    'wld_rgn'
  ];
  
  // Create object with all properties, defaulting to 0 if missing
  var updates = {};
  propertyNames.forEach(function(name) {
    updates[name] = ee.Algorithms.If(ft.get(name), ft.get(name), 0);
  });
  
  return ft.set(updates);
});

// print('multiStats', multiStats);

Export.table.toDrive({
  collection: multiStats,
  folder: 'csv_countries_2026-1-8',
  description: imgDamageRegion+'_GDP_2026-1-8',
  fileFormat: 'CSV'
});