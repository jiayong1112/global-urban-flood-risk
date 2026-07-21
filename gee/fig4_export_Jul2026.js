var rtg_Shanghai = 
    /* color: #d63000 */
    /* shown: false */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[119.65684593615288, 32.262837994343684],
          [119.65684593615288, 30.78558758986796],
          [122.04911888537163, 30.78558758986796],
          [122.04911888537163, 32.262837994343684]]], null, false),
    rtg_Guangzhou = 
    /* color: #98ff00 */
    /* shown: false */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[112.53174290759176, 23.50452504007198],
          [112.53174290759176, 22.59217001055901],
          [113.86795506579489, 22.59217001055901],
          [113.86795506579489, 23.50452504007198]]], null, false),
    rtg_Bangkok = 
    /* color: #0b4a8b */
    /* shown: false */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[99.84302818137097, 14.379045237719223],
          [99.84302818137097, 13.437939834553003],
          [101.2121993239491, 13.437939834553003],
          [101.2121993239491, 14.379045237719223]]], null, false),
    rtg_Dhaka = 
    /* color: #ffc82d */
    /* shown: false */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[89.62986289816784, 24.13694436395852],
          [89.62986289816784, 23.25418166240805],
          [91.0004073317616, 23.25418166240805],
          [91.0004073317616, 24.13694436395852]]], null, false);
// https://docs.google.com/presentation/d/1fjwqzUmhs4kzGzPQVoveriFXR_eVPUnHRCoIEohCrK8/edit?slide=id.g3c9b5cb236b_0_0#slide=id.g3c9b5cb236b_0_0
// Figure 4 regeneration, step 1 of 2 (Jul 2026 revision).
// Exports, per city: (1) the three risk bands (IR-AED, FD-AED, FD-AED-P) at 100 m,
// and (2) a cloud-free Sentinel-2 RGB composite at 10 m (open Copernicus data,
// replacing the Google basemap that cannot be published under CC BY).
// Step 2: code/figures/fig4_city_maps_2026-7.py composes the print figure locally
// with an in-map legend, scale bar, and city-center marker (reviewer request).
//
// Run in the Code Editor, start all 8 tasks, then download the GeoTIFFs from
// Drive folder "fig4_tiffs_2026-7" into the project folder data/fig4_tiffs/.
//
// IMPORTANT: adjust the city rectangles below to match the extents used in the
// submitted Figure 4 before running.

var floodRisk = ee.Image("users/Jiayong_Liang/Research_projects/FloodRiskViewGlobal_Jan2026_bh-JRC")
                  .select(['exInunD', 'exDmg', 'exDmg_pros']);

var cities = {
  Shanghai:  rtg_Shanghai,
  Guangzhou: rtg_Guangzhou,
  Bangkok:   rtg_Bangkok,
  Dhaka:     rtg_Dhaka
};

// var cities = {
//   Shanghai:  ee.Geometry.Rectangle([121.10, 30.85, 121.95, 31.50]),
//   Guangzhou: ee.Geometry.Rectangle([112.95, 22.75, 113.65, 23.40]),
//   Bangkok:   ee.Geometry.Rectangle([100.25, 13.45, 100.95, 14.10]),
//   Dhaka:     ee.Geometry.Rectangle([90.20, 23.55, 90.60, 24.00])
// };

function s2Composite(region) {
  return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(region)
    .filterDate('2020-01-01', '2024-12-31')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
    .map(function (img) {
      var scl = img.select('SCL');
      var clear = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10));
      return img.updateMask(clear);
    })
    .median()
    .select(['B4', 'B3', 'B2'])
    .clip(region);
}

Object.keys(cities).forEach(function (name) {
  var region = cities[name];

  Export.image.toDrive({
    image: floodRisk.toFloat().clip(region),
    description: name + '_risk_2026-7',
    folder: 'fig4_tiffs_2026-7',
    region: region,
    scale: 100,
    crs: 'EPSG:4326',
    maxPixels: 1e9
  });

  Export.image.toDrive({
    image: s2Composite(region).toUint16(),
    description: name + '_s2rgb_2026-7',
    folder: 'fig4_tiffs_2026-7',
    region: region,
    scale: 10,
    crs: 'EPSG:4326',
    maxPixels: 1e10
  });

  Map.addLayer(s2Composite(region), {min: 0, max: 2500, gamma: 1.2}, name + ' S2', false);
  Map.addLayer(floodRisk.clip(region),
    {bands: ["exInunD", "exDmg", "exDmg_pros"], min: 0.1, max: 0.01},
    name + ' risk composite (IR-AED red, FD-AED-P green, FD-AED blue)', false);
});

var imageVisParam_3view = {
  "opacity": 1,
  "bands": ["exInunD", "exDmg", "exDmg_pros"],
  "min": 0.1,
  "max": 0.01,
  "gamma": 1
};

// Caption attribution for the manuscript:
// "Background imagery: cloud-free Sentinel-2 surface reflectance composite
//  (contains modified Copernicus Sentinel data 2020-2024), composited by the
//  authors. Maps created in Google Earth Engine (https://earthengine.google.com)."
