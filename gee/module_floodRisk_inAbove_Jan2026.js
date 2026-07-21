//rp10, rp20, rp50, rp100, rp200, rp500, height, volume, footprint, flopros_model, flopros_merge
// with updated dataset Jan 6, 2026

var FloodHazard = ee.ImageCollection('JRC/CEMS_GLOFAS/FloodHazard/v2_1'),
    rp100 = FloodHazard.select('RP100_depth').mosaic(),
    rp10  = FloodHazard.select('RP10_depth').mosaic(),
    rp200 = FloodHazard.select('RP200_depth').mosaic(),
    rp20  = FloodHazard.select('RP20_depth').mosaic(),
    rp500 = FloodHazard.select('RP500_depth').mosaic(),
    rp50  = FloodHazard.select('RP50_depth').mosaic(),
    
    // Updated building height data (resolution 100m)
    // height = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_H/2018").select('built_height'),
    height = ee.Image("projects/ee-knhuang/assets/WSF3D_V02_90m").divide(10),
    // height = ee.Image("projects/ee-knhuang/assets/GBH2020_150m"),
    
    // previous building height data (resolution 1000m)
    height_ch = ee.Image("users/Jiayong_Liang/Reference_Dataset/Built-up_3D/cn_h_c_mn"),
    height_cv = ee.Image("users/Jiayong_Liang/Reference_Dataset/Built-up_3D/height_cv"),
    FLOPROS = ee.FeatureCollection("users/Jiayong_Liang/Reference_Dataset/FLOPROS_shp_V1"),
    //height = ee.Image("users/Jiayong_Liang/Reference_Dataset/Built-up_3D/height_mean"),
    volume = ee.Image("users/Jiayong_Liang/Reference_Dataset/Built-up_3D/volume_mean"),
    footprint = ee.Image("users/Jiayong_Liang/Reference_Dataset/Built-up_3D/footprint_mean"),
    
    continent = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017"),
    flopros_model = ee.Image("users/Jiayong_Liang/Research_projects/FLOPROS_model"),
    flopros_merge = ee.Image("users/Jiayong_Liang/Research_projects/FLOPROS_merge");


/**
 * Function to return result full output image of input building characteristics,
 * expected water depth, damage, depth over building height
 * @param {ee.Image} 
 * flopros_imageType:    "flopros_model"     "flopros_merge"
 * damageImageType: img_damage_Asia   img_damage_NAmerica  img_damage_Europe 
 *                 img_damage_Africa img_damage_CSAmerica img_damage_Oceania
 * @return {ee.Image} result image 
 */
exports.expected_annual_flood_risk_fullOut = function(flopros_imageType, damageImageType){
// --------------------------------------------- 1 ---------------------------------------------
// Combine hazard (flood depth), and building statistics
// Flood depth as hazard
var hazard = rp10.rename('depth_10').addBands(rp20.rename('depth_20'))
            .addBands(rp50.rename('depth_50')).addBands(rp100.rename('depth_100'))
            .addBands(rp200.rename('depth_200')).addBands(rp500.rename('depth_500'));

// inundation ratio to (1) height, and (2) volume data from the RSE paper
var inun_depthR = hazard.divide(height).rename(['inunD_10',  'inunD_20',  'inunD_50',
                                                'inunD_100', 'inunD_200', 'inunD_500']);
var maskD_lte1 = inun_depthR.lte(1)
var maskD_gt1 = inun_depthR.gt(1)
// cap the ratio between 0 to 1
var inun_depthR_cap = inun_depthR.multiply(maskD_lte1).add(maskD_gt1);
                                                     
var inun_volumeR = hazard.multiply(footprint).divide(volume).rename(['inunV_10', 'inunV_20', 'inunV_50',
                                                                     'inunV_100', 'inunV_200', 'inunV_500']);
var maskV_lte1 = inun_volumeR.lte(1)
var maskV_gt1 = inun_volumeR.gt(1)
var inun_volumeR_cap = inun_volumeR.multiply(maskV_lte1).add(maskV_gt1); 

// --------------------------------------------- 2 ---------------------------------------------
// Damage function different by continent
// Europe
var damageThresholds_Europe = ee.Image([0.2, 0.6, 0.9, 1.2, 1.8, 2.2, 2.8, 3.4, 4.2, 5.5]);

var damageEurope_RP10 = rp10.gt(damageThresholds_Europe).reduce('sum').rename('damage_10');
var damageEurope_RP20 = rp20.gt(damageThresholds_Europe).reduce('sum').rename('damage_20');
var damageEurope_RP50 = rp50.gt(damageThresholds_Europe).reduce('sum').rename('damage_50');
var damageEurope_RP100 = rp100.gt(damageThresholds_Europe).reduce('sum').rename('damage_100');
var damageEurope_RP200 = rp200.gt(damageThresholds_Europe).reduce('sum').rename('damage_200');
var damageEurope_RP500 = rp500.gt(damageThresholds_Europe).reduce('sum').rename('damage_500');

var totalDamage_Europe = damageEurope_RP10.addBands(damageEurope_RP20)
    .addBands(damageEurope_RP50).addBands(damageEurope_RP100)
    .addBands(damageEurope_RP200).addBands(damageEurope_RP500).divide(10);

// North America
var damageThresholds_NAmerica = ee.Image([0.1, 0.25, 0.4, 0.65, 1, 1.5, 2, 3, 4, 6]);

var damageNAmerica_RP10 = rp10.gt(damageThresholds_NAmerica).reduce('sum').rename('damage_10');
var damageNAmerica_RP20 = rp20.gt(damageThresholds_NAmerica).reduce('sum').rename('damage_20');
var damageNAmerica_RP50 = rp50.gt(damageThresholds_NAmerica).reduce('sum').rename('damage_50');
var damageNAmerica_RP100 = rp100.gt(damageThresholds_NAmerica).reduce('sum').rename('damage_100');
var damageNAmerica_RP200 = rp200.gt(damageThresholds_NAmerica).reduce('sum').rename('damage_200');
var damageNAmerica_RP500 = rp500.gt(damageThresholds_NAmerica).reduce('sum').rename('damage_500');

var totalDamage_NAmerica = damageNAmerica_RP10.addBands(damageNAmerica_RP20)
    .addBands(damageNAmerica_RP50).addBands(damageNAmerica_RP100)
    .addBands(damageNAmerica_RP200).addBands(damageNAmerica_RP500).divide(10);

// Central and South America
var damageThresholds_CSAmerica = ee.Image([0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.8, 1, 1.5, 3]);

var damageCSAmerica_RP10 = rp10.gt(damageThresholds_CSAmerica).reduce('sum').rename('damage_10');
var damageCSAmerica_RP20 = rp20.gt(damageThresholds_CSAmerica).reduce('sum').rename('damage_20');
var damageCSAmerica_RP50 = rp50.gt(damageThresholds_CSAmerica).reduce('sum').rename('damage_50');
var damageCSAmerica_RP100 = rp100.gt(damageThresholds_CSAmerica).reduce('sum').rename('damage_100');
var damageCSAmerica_RP200 = rp200.gt(damageThresholds_CSAmerica).reduce('sum').rename('damage_200');
var damageCSAmerica_RP500 = rp500.gt(damageThresholds_CSAmerica).reduce('sum').rename('damage_500');

var totalDamage_CSAmerica = damageCSAmerica_RP10.addBands(damageCSAmerica_RP20)
    .addBands(damageCSAmerica_RP50).addBands(damageCSAmerica_RP100)
    .addBands(damageCSAmerica_RP200).addBands(damageCSAmerica_RP500).divide(10);

// Asia
var damageThresholds_Asia = ee.Image([0.1, 0.2, 0.4, 0.8, 1, 1.4, 1.8, 2.5, 3.6, 5.5]);

var damageAsia_RP10 = rp10.gt(damageThresholds_Asia).reduce('sum').rename('damage_10');
var damageAsia_RP20 = rp20.gt(damageThresholds_Asia).reduce('sum').rename('damage_20');
var damageAsia_RP50 = rp50.gt(damageThresholds_Asia).reduce('sum').rename('damage_50');
var damageAsia_RP100 = rp100.gt(damageThresholds_Asia).reduce('sum').rename('damage_100');
var damageAsia_RP200 = rp200.gt(damageThresholds_Asia).reduce('sum').rename('damage_200');
var damageAsia_RP500 = rp500.gt(damageThresholds_Asia).reduce('sum').rename('damage_500');

var totalDamage_Asia = damageAsia_RP10.addBands(damageAsia_RP20)
    .addBands(damageAsia_RP50).addBands(damageAsia_RP100)
    .addBands(damageAsia_RP200).addBands(damageAsia_RP500).divide(10);

// Africa
var damageThresholds_Africa = ee.Image([0.4, 0.7, 1, 1.4, 1.6, 2.2, 2.8, 3.2, 4, 5.5]);

var damageAfrica_RP10 = rp10.gt(damageThresholds_Africa).reduce('sum').rename('damage_10');
var damageAfrica_RP20 = rp20.gt(damageThresholds_Africa).reduce('sum').rename('damage_20');
var damageAfrica_RP50 = rp50.gt(damageThresholds_Africa).reduce('sum').rename('damage_50');
var damageAfrica_RP100 = rp100.gt(damageThresholds_Africa).reduce('sum').rename('damage_100');
var damageAfrica_RP200 = rp200.gt(damageThresholds_Africa).reduce('sum').rename('damage_200');
var damageAfrica_RP500 = rp500.gt(damageThresholds_Africa).reduce('sum').rename('damage_500');

var totalDamage_Africa = damageAfrica_RP10.addBands(damageAfrica_RP20)
    .addBands(damageAfrica_RP50).addBands(damageAfrica_RP100)
    .addBands(damageAfrica_RP200).addBands(damageAfrica_RP500).divide(10);

// Oceania
var damageThresholds_Oceania = ee.Image([0.2, 0.3, 0.4, 0.6, 0.8, 1.2, 1.5, 1.9, 2.6, 5]);

var damageOceania_RP10 = rp10.gt(damageThresholds_Oceania).reduce('sum').rename('damage_10');
var damageOceania_RP20 = rp20.gt(damageThresholds_Oceania).reduce('sum').rename('damage_20');
var damageOceania_RP50 = rp50.gt(damageThresholds_Oceania).reduce('sum').rename('damage_50');
var damageOceania_RP100 = rp100.gt(damageThresholds_Oceania).reduce('sum').rename('damage_100');
var damageOceania_RP200 = rp200.gt(damageThresholds_Oceania).reduce('sum').rename('damage_200');
var damageOceania_RP500 = rp500.gt(damageThresholds_Oceania).reduce('sum').rename('damage_500');

var totalDamage_Oceania = damageOceania_RP10.addBands(damageOceania_RP20)
    .addBands(damageOceania_RP50).addBands(damageOceania_RP100)
    .addBands(damageOceania_RP200).addBands(damageOceania_RP500).divide(10);
    

// --------------------------------------------- 3 ---------------------------------------------    
// Combine hazard and damage function
// depth-damge curve different for different continent
var img_damage_Europe = height.rename('h').addBands(volume.rename('v')).addBands(footprint.rename('f'))
          .addBands(hazard).addBands(totalDamage_Europe).addBands(inun_depthR_cap).addBands(inun_volumeR_cap);
          
var img_damage_NAmerica = height.rename('h').addBands(volume.rename('v')).addBands(footprint.rename('f'))
          .addBands(hazard).addBands(totalDamage_NAmerica).addBands(inun_depthR_cap).addBands(inun_volumeR_cap);
          
var img_damage_CSAmerica = height.rename('h').addBands(volume.rename('v')).addBands(footprint.rename('f'))
          .addBands(hazard).addBands(totalDamage_CSAmerica).addBands(inun_depthR_cap).addBands(inun_volumeR_cap);
          
var img_damage_Asia = height.rename('h').addBands(volume.rename('v')).addBands(footprint.rename('f'))
          .addBands(hazard).addBands(totalDamage_Asia).addBands(inun_depthR_cap).addBands(inun_volumeR_cap);
          
var img_damage_Africa = height.rename('h').addBands(volume.rename('v')).addBands(footprint.rename('f'))
          .addBands(hazard).addBands(totalDamage_Africa).addBands(inun_depthR_cap).addBands(inun_volumeR_cap);
          
var img_damage_Oceania = height.rename('h').addBands(volume.rename('v')).addBands(footprint.rename('f'))
          .addBands(hazard).addBands(totalDamage_Oceania).addBands(inun_depthR_cap).addBands(inun_volumeR_cap);    
    
// --------------------------------------------- 4 ---------------------------------------------
// A function to calculate expected damage without any protection
var calculate_expectedDamage = function(img) {
  var b_expected_depth = img.select('depth_500').add(img.select('depth_200')).multiply(0.003).divide(2)
                   .add(img.select('depth_200').add(img.select('depth_100')).multiply(0.005).divide(2))
                   .add(img.select('depth_100').add(img.select('depth_50')).multiply(0.01).divide(2))
                   .add(img.select('depth_50').add(img.select('depth_20')).multiply(0.03).divide(2))
                   .add(img.select('depth_20').add(img.select('depth_10')).multiply(0.05).divide(2))
                   .rename('exDep')
                   
  var b_expected_damage = img.select('damage_500').add(img.select('damage_200')).multiply(0.003).divide(2)
                   .add(img.select('damage_200').add(img.select('damage_100')).multiply(0.005).divide(2))
                   .add(img.select('damage_100').add(img.select('damage_50')).multiply(0.01).divide(2))
                   .add(img.select('damage_50').add(img.select('damage_20')).multiply(0.03).divide(2))
                   .add(img.select('damage_20').add(img.select('damage_10')).multiply(0.05).divide(2))
                   .rename('exDmg')
                   
  var b_expected_inunD = img.select('inunD_500').add(img.select('inunD_200')).multiply(0.003).divide(2)
                   .add(img.select('inunD_200').add(img.select('inunD_100')).multiply(0.005).divide(2))
                   .add(img.select('inunD_100').add(img.select('inunD_50')).multiply(0.01).divide(2))
                   .add(img.select('inunD_50').add(img.select('inunD_20')).multiply(0.03).divide(2))
                   .add(img.select('inunD_20').add(img.select('inunD_10')).multiply(0.05).divide(2))
                   .rename('exInunD')
                   
  var b_expected_inunV = img.select('inunV_500').add(img.select('inunV_200')).multiply(0.003).divide(2)
                   .add(img.select('inunV_200').add(img.select('inunV_100')).multiply(0.005).divide(2))
                   .add(img.select('inunV_100').add(img.select('inunV_50')).multiply(0.01).divide(2))
                   .add(img.select('inunV_50').add(img.select('inunV_20')).multiply(0.03).divide(2))
                   .add(img.select('inunV_20').add(img.select('inunV_10')).multiply(0.05).divide(2))
                   .rename('exInunV')                 
                   
  var expected = b_expected_depth.addBands(b_expected_damage).addBands(b_expected_inunD).addBands(b_expected_inunV)
  return expected
}  
    
// --------------------------------------------- 5 ---------------------------------------------
// A function to calculate expected damage consider protection standards (in years)
// (1) model layer, (2) merge layer consider engineer or legal documents
//var protectYear = flopros_model; // ----------------------------- can be changed to different years such as the merged layer
var protectYear;
if (flopros_imageType === 'flopros_model') {
    protectYear = flopros_model;
  } else if (flopros_imageType === 'flopros_merge') {
    protectYear = flopros_merge;
  } else {
    throw new Error('Invalid image type provided. Use "flopros_model" or "flopros_merge".');
  }

var fpm_10 = protectYear.selfMask().lt(10);
var fpm_20 = (protectYear.selfMask().gte(10)).and(protectYear.selfMask().lt(20));
var fpm_50 = (protectYear.selfMask().gte(20)).and(protectYear.selfMask().lt(50));
var fpm_100 = (protectYear.selfMask().gte(50)).and(protectYear.selfMask().lt(100));
var fpm_200 = (protectYear.selfMask().gte(100)).and(protectYear.selfMask().lt(200));
var fpm_500 = (protectYear.selfMask().gte(200)).and(protectYear.selfMask().lt(500));
var fpm_500Plus = protectYear.selfMask().gte(500);


var calculate_expectedDamage_pros10 = function(img) {
  var b_expected_depth = img.select('depth_500').add(img.select('depth_200')).multiply(0.003).divide(2)
                   .add(img.select('depth_200').add(img.select('depth_100')).multiply(0.005).divide(2))
                   .add(img.select('depth_100').add(img.select('depth_50')).multiply(0.01).divide(2))
                   .add(img.select('depth_50').add(img.select('depth_20')).multiply(0.03).divide(2))
                   .add(img.select('depth_20').add(img.select('depth_10')).multiply(0.05).divide(2))
                   .rename('exDep')
                   
  var b_expected_damage = img.select('damage_500').add(img.select('damage_200')).multiply(0.003).divide(2)
                   .add(img.select('damage_200').add(img.select('damage_100')).multiply(0.005).divide(2))
                   .add(img.select('damage_100').add(img.select('damage_50')).multiply(0.01).divide(2))
                   .add(img.select('damage_50').add(img.select('damage_20')).multiply(0.03).divide(2))
                   .add(img.select('damage_20').add(img.select('damage_10')).multiply(0.05).divide(2))
                   .rename('exDmg')
                   
  var b_expected_inunD = img.select('inunD_500').add(img.select('inunD_200')).multiply(0.003).divide(2)
                   .add(img.select('inunD_200').add(img.select('inunD_100')).multiply(0.005).divide(2))
                   .add(img.select('inunD_100').add(img.select('inunD_50')).multiply(0.01).divide(2))
                   .add(img.select('inunD_50').add(img.select('inunD_20')).multiply(0.03).divide(2))
                   .add(img.select('inunD_20').add(img.select('inunD_10')).multiply(0.05).divide(2))
                   .rename('exInunD')
                   
  var b_expected_inunV = img.select('inunV_500').add(img.select('inunV_200')).multiply(0.003).divide(2)
                   .add(img.select('inunV_200').add(img.select('inunV_100')).multiply(0.005).divide(2))
                   .add(img.select('inunV_100').add(img.select('inunV_50')).multiply(0.01).divide(2))
                   .add(img.select('inunV_50').add(img.select('inunV_20')).multiply(0.03).divide(2))
                   .add(img.select('inunV_20').add(img.select('inunV_10')).multiply(0.05).divide(2))
                   .rename('exInunV')                 
                   
  var expected = b_expected_depth.addBands(b_expected_damage).addBands(b_expected_inunD).addBands(b_expected_inunV)
  return expected
}

var calculate_expectedDamage_pros20 = function(img) {
  var b_expected_depth = img.select('depth_500').add(img.select('depth_200')).multiply(0.003).divide(2)
                   .add(img.select('depth_200').add(img.select('depth_100')).multiply(0.005).divide(2))
                   .add(img.select('depth_100').add(img.select('depth_50')).multiply(0.01).divide(2))
                   .add(img.select('depth_50').add(img.select('depth_20')).multiply(0.03).divide(2))
                   .rename('exDep')
                   
  var b_expected_damage = img.select('damage_500').add(img.select('damage_200')).multiply(0.003).divide(2)
                   .add(img.select('damage_200').add(img.select('damage_100')).multiply(0.005).divide(2))
                   .add(img.select('damage_100').add(img.select('damage_50')).multiply(0.01).divide(2))
                   .add(img.select('damage_50').add(img.select('damage_20')).multiply(0.03).divide(2))
                   .rename('exDmg')
                   
  var b_expected_inunD = img.select('inunD_500').add(img.select('inunD_200')).multiply(0.003).divide(2)
                   .add(img.select('inunD_200').add(img.select('inunD_100')).multiply(0.005).divide(2))
                   .add(img.select('inunD_100').add(img.select('inunD_50')).multiply(0.01).divide(2))
                   .add(img.select('inunD_50').add(img.select('inunD_20')).multiply(0.03).divide(2))
                   .rename('exInunD')
                   
  var b_expected_inunV = img.select('inunV_500').add(img.select('inunV_200')).multiply(0.003).divide(2)
                   .add(img.select('inunV_200').add(img.select('inunV_100')).multiply(0.005).divide(2))
                   .add(img.select('inunV_100').add(img.select('inunV_50')).multiply(0.01).divide(2))
                   .add(img.select('inunV_50').add(img.select('inunV_20')).multiply(0.03).divide(2))
                   .rename('exInunV')                 
                   
  var expected = b_expected_depth.addBands(b_expected_damage).addBands(b_expected_inunD).addBands(b_expected_inunV)
  return expected
}

var calculate_expectedDamage_pros50 = function(img) {
  var b_expected_depth = img.select('depth_500').add(img.select('depth_200')).multiply(0.003).divide(2)
                   .add(img.select('depth_200').add(img.select('depth_100')).multiply(0.005).divide(2))
                   .add(img.select('depth_100').add(img.select('depth_50')).multiply(0.01).divide(2))
                   .rename('exDep')
                   
  var b_expected_damage = img.select('damage_500').add(img.select('damage_200')).multiply(0.003).divide(2)
                   .add(img.select('damage_200').add(img.select('damage_100')).multiply(0.005).divide(2))
                   .add(img.select('damage_100').add(img.select('damage_50')).multiply(0.01).divide(2))
                   .rename('exDmg')
                   
  var b_expected_inunD = img.select('inunD_500').add(img.select('inunD_200')).multiply(0.003).divide(2)
                   .add(img.select('inunD_200').add(img.select('inunD_100')).multiply(0.005).divide(2))
                   .add(img.select('inunD_100').add(img.select('inunD_50')).multiply(0.01).divide(2))
                   .rename('exInunD')
                   
  var b_expected_inunV = img.select('inunV_500').add(img.select('inunV_200')).multiply(0.003).divide(2)
                   .add(img.select('inunV_200').add(img.select('inunV_100')).multiply(0.005).divide(2))
                   .add(img.select('inunV_100').add(img.select('inunV_50')).multiply(0.01).divide(2))
                   .rename('exInunV')                 
                   
  var expected = b_expected_depth.addBands(b_expected_damage).addBands(b_expected_inunD).addBands(b_expected_inunV)
  return expected
}

var calculate_expectedDamage_pros100 = function(img) {
  var b_expected_depth = img.select('depth_500').add(img.select('depth_200')).multiply(0.003).divide(2)
                   .add(img.select('depth_200').add(img.select('depth_100')).multiply(0.005).divide(2))
                   .rename('exDep')
                   
  var b_expected_damage = img.select('damage_500').add(img.select('damage_200')).multiply(0.003).divide(2)
                   .add(img.select('damage_200').add(img.select('damage_100')).multiply(0.005).divide(2))
                   .rename('exDmg')
                   
  var b_expected_inunD = img.select('inunD_500').add(img.select('inunD_200')).multiply(0.003).divide(2)
                   .add(img.select('inunD_200').add(img.select('inunD_100')).multiply(0.005).divide(2))
                   .rename('exInunD')
                   
  var b_expected_inunV = img.select('inunV_500').add(img.select('inunV_200')).multiply(0.003).divide(2)
                   .add(img.select('inunV_200').add(img.select('inunV_100')).multiply(0.005).divide(2))
                   .rename('exInunV')                 
                   
  var expected = b_expected_depth.addBands(b_expected_damage).addBands(b_expected_inunD).addBands(b_expected_inunV)
  return expected
}

var calculate_expectedDamage_pros200 = function(img) {
  var b_expected_depth = img.select('depth_500').add(img.select('depth_200')).multiply(0.003).divide(2)
                   .rename('exDep')
                   
  var b_expected_damage = img.select('damage_500').add(img.select('damage_200')).multiply(0.003).divide(2)
                   .rename('exDmg')
                   
  var b_expected_inunD = img.select('inunD_500').add(img.select('inunD_200')).multiply(0.003).divide(2)
                   .rename('exInunD')
                   
  var b_expected_inunV = img.select('inunV_500').add(img.select('inunV_200')).multiply(0.003).divide(2)
                   .rename('exInunV')                 
                   
  var expected = b_expected_depth.addBands(b_expected_damage).addBands(b_expected_inunD).addBands(b_expected_inunV)
  return expected
}

var calculate_expectedDamage_pros500 = function(img) {
  var b_expected_depth = img.select('depth_500').divide(500)
                   .rename('exDep')
                   
  var b_expected_damage = img.select('damage_500').divide(500)
                   .rename('exDmg')
                   
  var b_expected_inunD = img.select('inunD_500').divide(500)
                   .rename('exInunD')
                   
  var b_expected_inunV = img.select('inunV_500').divide(500)
                   .rename('exInunV')                 
                   
  var expected = b_expected_depth.addBands(b_expected_damage).addBands(b_expected_inunD).addBands(b_expected_inunV)
  return expected
}

// assumption of expected damage >500 year // ----------------------------- can be changed, depends on data availability
var calculate_expectedDamage_pros500Plus = function(img) {
  var b_expected_depth = img.select('depth_500').divide(1000)
                   .rename('exDep')
                   
  var b_expected_damage = img.select('damage_500').divide(1000)
                   .rename('exDmg')
                   
  var b_expected_inunD = img.select('inunD_500').divide(1000)
                   .rename('exInunD')
                   
  var b_expected_inunV = img.select('inunV_500').divide(1000)
                   .rename('exInunV')                 
                   
  var expected = b_expected_depth.addBands(b_expected_damage).addBands(b_expected_inunD).addBands(b_expected_inunV)
  return expected
}
   
// --------------------------------------------- 5 ---------------------------------------------
// Combine and return the result image
//var expectedDamage = img_damage_Asia; // ------------------------------------------------------------------------------------------ change to other regions
// img_damage_Asia img_damage_NAmerica img_damage_Europe img_damage_Africa img_damage_CSAmerica img_damage_Oceania
var expectedDamage;
if (damageImageType === 'img_damage_Asia') {
    expectedDamage = img_damage_Asia;
  } else if (damageImageType === 'img_damage_NAmerica') {
    expectedDamage = img_damage_NAmerica;
  } else if (damageImageType === 'img_damage_Europe') {
    expectedDamage = img_damage_Europe;
  } else if (damageImageType === 'img_damage_Africa') {
    expectedDamage = img_damage_Africa;
  } else if (damageImageType === 'img_damage_CSAmerica') {
    expectedDamage = img_damage_CSAmerica;
  } else if (damageImageType === 'img_damage_Oceania') {
    expectedDamage = img_damage_Oceania;
  } else {
    throw new Error('Invalid damage image type provided. Use "img_damage_Asia", "img_damage_NAmerica", "img_damage_Europe", "img_damage_Africa", "img_damage_CSAmerica", or "img_damage_Oceania".');
  }

var expectedDamage_wProtect = calculate_expectedDamage_pros10(expectedDamage.multiply(fpm_10))
              .add(calculate_expectedDamage_pros20(expectedDamage.multiply(fpm_20)))
              .add(calculate_expectedDamage_pros50(expectedDamage.multiply(fpm_50)))
              .add(calculate_expectedDamage_pros100(expectedDamage.multiply(fpm_100)))
              .add(calculate_expectedDamage_pros200(expectedDamage.multiply(fpm_200)))
              .add(calculate_expectedDamage_pros500(expectedDamage.multiply(fpm_500)))
              .add(calculate_expectedDamage_pros500Plus(expectedDamage.multiply(fpm_500Plus)))
              .rename(["exDep_pros","exDmg_pros","exInunD_pros","exInunV_pros"]);
                       
// ---------------------------------------------------------------
var mergedDamage = calculate_expectedDamage(expectedDamage).addBands(expectedDamage_wProtect);

var mergedDamage_footprintWeighted = mergedDamage.multiply(footprint)
                                       .rename(["exDep_fp","exDmg_fp","exInunD_fp","exInunV_fp",
                                                "exDep_prosp_fp","exDmg_prosp_fp","exInunD_prosp_fp","exInunV_prosp_fp"])
                                       .addBands(footprint.rename('footprint'))
                                       .addBands(height.rename('height'))
                                       .addBands(volume.rename('volume'))
                                       .addBands(flopros_model.rename('flopros_model'))
                                       .addBands(flopros_merge.rename('flopros_merge'));

var img2exp = mergedDamage.addBands(mergedDamage_footprintWeighted);

// general building exposure in floodplain
var temp1 = img2exp.select('exDep').gt(0)
                .multiply(img2exp.select('footprint'))
                .rename('flood_FP')
var temp2 = img2exp.select('exDep').gt(0)
                .multiply(img2exp.select('volume'))
                .rename('flood_VL')
img2exp = img2exp.addBands(temp1).addBands(temp2)   

return img2exp.unmask()    
// return img2exp.select(["exDmg","exInunD","exDmg_pros","exInunD_pros"])
   
}
