/**** Start of imports. If edited, may not auto-convert in the playground. ****/
var fua = ee.FeatureCollection("users/Jiayong_Liang/Research_projects/FUA2015_100Mpop"),
    globalRegion = 
    /* color: #d63000 */
    /* shown: false */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[-168.71189425790027, 77.91566898632581],
          [-168.71189425790027, -57.70414723434183],
          [174.41310574209956, -57.70414723434183],
          [174.41310574209956, 77.91566898632581]]], null, false);
/***** End of imports. If edited, may not auto-convert in the playground. *****/
// import the function modules
var floodRisk = require('users/Jiayong_Liang/research_projects:Modules/floodRisk_inAbove_Jan2026')

/**
 * Function to return result image of expected water depth, damage, depth over building height
 * expected_annual_flood_risk = function(protectYear, expectedDamage)
 * @param {ee.Image} 
 * floodProtectLayer:    flopros_model     flopros_merge
 * imgDamageRegion: img_damage_Asia   img_damage_NAmerica  img_damage_Europe 
 *                 img_damage_Africa img_damage_CSAmerica img_damage_Oceania
 * @return {ee.Image} result image 
 */
var floodProtectLayer = "flopros_model"
var imgDamageRegion = "img_damage_Asia"

var LSIB_SIMPLE = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017');
  
/**
 * Function to set region collection filter based on the expectedDamage parameter
 * @param {String} expectedDamage - Expected damage image identifier
 * @return {ee.FeatureCollection} - Filtered region collection
 */
function getRegionCol(expectedDamage) {
  
  var regionCol = LSIB_SIMPLE;
  
  switch (expectedDamage) {
    case 'img_damage_NAmerica':
      regionCol = regionCol.filter(ee.Filter.eq('wld_rgn', 'North America'));
      break;
    case 'img_damage_Asia':
      regionCol = regionCol.filter(ee.Filter.or(
        ee.Filter.eq('wld_rgn', 'E Asia'),
        ee.Filter.eq('wld_rgn', 'S Asia'),
        ee.Filter.eq('wld_rgn', 'SE Asia'),
        ee.Filter.eq('wld_rgn', 'SW Asia'),
        ee.Filter.eq('wld_rgn', 'N Asia'),
        ee.Filter.eq('wld_rgn', 'Central Asia')
      ));
      break;
    case 'img_damage_Europe':
      regionCol = regionCol.filter(ee.Filter.eq('wld_rgn', 'Europe'));
      break;
    case 'img_damage_Africa':
      regionCol = regionCol.filter(ee.Filter.eq('wld_rgn', 'Africa'));
      break;
    case 'img_damage_CSAmerica':
      regionCol = regionCol.filter(ee.Filter.or(
        ee.Filter.eq('wld_rgn', 'South America'),
        ee.Filter.eq('wld_rgn', 'Central America')
      ));
      break;
    case 'img_damage_Oceania':
      regionCol = regionCol.filter(ee.Filter.or(
        ee.Filter.eq('wld_rgn', 'Oceania'),
        ee.Filter.eq('wld_rgn', 'Australia')
      ));
      break;
  }
  
  return regionCol;
}

//var bandList = ['exDmg','exDmg_pros', 'exInunD'];

function getAverageFloodRisk(imgDamageRegion) {
  
  var bandList = ['exDep', 'exDmg', 'exDmg_pros', 'exInunD', 'exInunD_pros',
                  'height',
                  'flopros_model', 'flopros_merge'];
  
  var modelFloodRisk_A = floodRisk.expected_annual_flood_risk_fullOut("flopros_model", imgDamageRegion).select(bandList);
  var mergeFloodRisk_A = floodRisk.expected_annual_flood_risk_fullOut("flopros_merge", imgDamageRegion).select(bandList);

  var aveFloodRisk_A = modelFloodRisk_A.add(mergeFloodRisk_A).divide(2).clip(getRegionCol(imgDamageRegion));
  
  return aveFloodRisk_A.unmask()
}

var aveFloodRisk_Asia = getAverageFloodRisk("img_damage_Asia");
var aveFloodRisk_NAmerica = getAverageFloodRisk("img_damage_NAmerica");
var aveFloodRisk_Europe = getAverageFloodRisk("img_damage_Europe");
var aveFloodRisk_Africa = getAverageFloodRisk("img_damage_Africa");
var aveFloodRisk_CSAmerica = getAverageFloodRisk("img_damage_CSAmerica");
var aveFloodRisk_Oceania = getAverageFloodRisk("img_damage_Oceania");

var aveFloodRisk = aveFloodRisk_Asia
              .add(aveFloodRisk_NAmerica)
              .add(aveFloodRisk_Europe)
              .add(aveFloodRisk_Africa)
              .add(aveFloodRisk_CSAmerica)
              .add(aveFloodRisk_Oceania)
// ==================================================================
var imageVisParam = {"opacity":0.3,
                    "bands":["exDmg"],
                    "min":0.005,"max":0.05,
                    "palette":["ffffff","06bee1","1768ac","2541b2","03256c"]};
                    

// Map.addLayer(aveFloodRisk, imageVisParam, 'aveFloodRisk')
// Map.addLayer(fua, {}, 'FUA', false)

// Mask the zero values, as view
var floodRisk_view = aveFloodRisk.updateMask(aveFloodRisk.neq(0));
                    
var imageVisParam_exDmg = {"opacity":1,
                    "bands":["exDmg"],
                    "min":0.005,"max":0.05,
                    "palette":["dddddd","7bb3d1","016eae"]}; // blue

var imageVisParam_exDmg_pros = {"opacity":1,
                    "bands":["exDmg_pros"],
                    "min":0.005,"max":0.05,
                    "palette":["dddddd","7bb3d1","016eae"]}; // blue
//                    "palette":["dddddd","af8e53","804d36"]}; // brown

var imageVisParam_exInunD = {"opacity":1,
                    "bands":["exInunD"],
                    "min":0.005,"max":0.05,
                    "palette":["dddddd","dd7c8a","cc0024"]}; // red
                    
var imageVisParam_3view = {"opacity":1,"bands":["exDep","exDmg","exInunD"],"min":0.005,"max":0.05,"gamma":1};

var imageVisParam_3view_pros = {"opacity":1,"bands":["exDep","exDmg_pros","exInunD_pros"],"min":0.0005,"max":0.005,"gamma":1};

                    
// // Add the masked image to the map
// Map.addLayer(floodRisk_view, imageVisParam_exDmg, 'Flood Risk View exDmg', false);
// Map.addLayer(floodRisk_view, imageVisParam_exDmg_pros, 'Flood Risk View exDmg_pros', false);
// Map.addLayer(floodRisk_view, imageVisParam_exInunD, 'Flood Risk View exInunD', false);

Map.addLayer(floodRisk_view, imageVisParam_3view, 'Flood Risk View composite');
// Map.addLayer(floodRisk_view, imageVisParam_3view_pros, 'Flood Risk View w/ Protection composite');

// --------------------------------------------------------------------
// Define the global region
// var globalRegion = ee.Geometry.Polygon(
//   [[[-180, -90], [-180, 90], [180, 90], [180, -90], [-180, -90]]]
// );

// Map.addLayer(globalRegion, {}, 'globalRegion')

// Export the image to an asset
Export.image.toAsset({
  image: floodRisk_view,
  description: 'FloodRiskViewGlobalExport', // A human-readable description
  assetId: 'users/Jiayong_Liang/Research_projects/FloodRiskViewGlobal_Jan2026_WSF3Dnew10', // The ID of the asset in your GEE assets
  region: globalRegion, // The region to export
  scale: 100, // The scale in meters per pixel
  maxPixels: 10000000000000 // The maximum number of pixels to include in the export
});
