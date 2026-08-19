/**flood_damage_exposure/temp_2026-08-13_stage2
 * STAGE2_diagnostics_fuaExport_2026-08.js
 *
 * Zonal statistics over the assets built by STAGE1_diagnostics_toAsset_2026-08.js.
 * This mirrors the original fuaExport_Jan2026.js, which reduced over the stored
 * FloodRiskViewGlobal_Jan26 asset rather than over a live computation.
 *
 * Because the image is already materialised, there is no expression tree to
 * evaluate per tile. No chunking, no band-group splitting, no tileScale games -
 * those were all treating a symptom of running the graph inside reduceRegions.
 *
 * HOW TO RUN
 *   1. Paste into a new Earth Engine script, Save, Run, then RUN ALL.
 *      One table export per region; all seven Stage 1 assets are ready.
 *   2. Download into
 *        revision-2026-08/analysis/csv_fua_diag_2026-08/
 *      alongside the CSVs that already succeeded, then run
 *        python a3_integration_diagnostics.py
 *
 * OCEANIA IS INCLUDED DELIBERATELY. It already has a CSV produced the old way,
 * by reducing over a live computation. Re-exporting it through the asset route
 * overwrites that file with values that should be identical. Compare the two
 * before trusting the other six: if Oceania matches, the asset route is sound.
 * Keep a copy of the existing JRC_Oceania_diag_2026-08.csv first.
 *
 * The other six sub-regions already downloaded (Australia, Central America,
 * Central Asia, N Asia, S Asia, SW Asia) do NOT need redoing.
 *
 * ONE DIFFERENCE FROM THE EARLIER CSVs: in Stage 1 the whole image, height
 * included, is masked to the 10-yr floodplain so the stored asset stays sparse.
 * In the earlier files height kept its own footprint. So height_mean means
 * something slightly different in the two sets - floodplain mean here, whole-FUA
 * mean there - and the two should not be pooled. No diagnostic uses height_mean;
 * the building heights quoted in the manuscript come from the archived 2026-1
 * exports, which are unaffected.
 */

// ===========================================================================
// CONFIG
// ===========================================================================
var DATASET = 'JRC';

// All seven Stage 1 assets are complete. Oceania first: it is one city and
// doubles as the cross-check against the CSV produced by the old route.
var REGIONS = ['Oceania', 'South America', 'North America', 'SE Asia',
               'Africa', 'Europe', 'E Asia'];

var ASSET_FOLDER  = 'projects/main-aviary-427701-f4/assets/Research_projects';
var ASSET_PREFIX = 'diag2026_08_';
var TILE_SCALE   = 4;      // materialised asset: the default is usually enough
// ===========================================================================

var fua = ee.FeatureCollection("users/Jiayong_Liang/Research_projects/FUA2015_100Mpop");
var LSIB_SIMPLE = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017');

function queueExport(region) {
  var tag = DATASET + '_' + region.replace(/ /g, '');
  var img = ee.Image(ASSET_FOLDER + '/' + ASSET_PREFIX + tag);

  var regionCol = LSIB_SIMPLE.filter(ee.Filter.eq('wld_rgn', region));
  var col = fua.filterBounds(regionCol.geometry(1000));

  var stats = img.reduceRegions({
    collection: col,
    reducer: ee.Reducer.mean().combine({
      reducer2: ee.Reducer.count(), sharedInputs: true
    }),
    scale: 100,
    tileScale: TILE_SCALE
  }).map(function (ft) { return ft.setGeometry(null); });

  Export.table.toDrive({
    collection: stats,
    folder: 'csv_fua_diag_2026-08',
    description: tag + '_diag_2026-08',
    fileFormat: 'CSV'
  });
  return tag;
}

var queued = REGIONS.map(queueExport);
print('Queued ' + queued.length + ' zonal-statistics tasks:', queued);
