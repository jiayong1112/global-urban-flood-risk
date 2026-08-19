/**
 * STAGE2c_diagnostics_fuaExport_2026-08.js
 *
 * WHY EUROPE AND NORTH AMERICA CAME BACK EMPTY
 *
 * Their CSVs contain every _count column and no _mean column at all. The
 * computation was fine; the export dropped them.
 *
 * Export.table.toDrive infers the CSV schema from the FIRST feature in the
 * collection. A feature with zero contributing pixels has no mean properties
 * set, so if it happens to sort first, every _mean column is omitted for the
 * whole table. The pattern is exact:
 *
 *   Europe        first feature Yerevan          0 px   -> no _mean columns
 *   North America first feature Port-au-Prince   0 px   -> no _mean columns
 *   Africa        first feature Cotonou      2,824 px   -> _mean columns present
 *   E Asia        first feature Hong Kong      212 px   -> _mean columns present
 *   SE Asia, South America, Oceania: likewise, all fine
 *
 * Yerevan and Port-au-Prince sit outside the JRC riverine floodplain, so zero
 * is the correct answer for them - they just poisoned the schema.
 *
 * THE FIX
 *
 * Pass `selectors` explicitly. The schema is then fixed by us rather than
 * inferred from whichever feature happens to come first, and zero-coverage
 * cities export as empty cells instead of deleting the columns.
 *
 * Nothing else changes: still reducing over the Stage 1 assets, still selecting
 * features from the asset footprint rather than dissolving country polygons.
 *
 * HOW TO RUN
 *   1. Europe and North America can run now - their Stage 1 assets exist.
 *   2. The six sub-regions never exported in the two-stage pipeline need their
 *      Stage 1 assets first. In STAGE1_diagnostics_toAsset_2026-08.js set
 *        var REGIONS = ['Australia', 'Central America', 'Central Asia',
 *                       'N Asia', 'SW Asia', 'S Asia'];
 *      run it, then add those names to REGIONS below and run this.
 *   3. Download into revision-2026-08/analysis/csv_fua_diag_2026-08/ and run
 *        python a3_integration_diagnostics.py
 *
 * Output names match Stage 2, so re-exported regions overwrite cleanly.
 */

// ===========================================================================
// CONFIG
// ===========================================================================
var DATASET = 'JRC';

// Ready now (Stage 1 assets exist):
var REGIONS = ['Europe', 'North America'];

// Add once their Stage 1 assets are built:
//   'Australia', 'Central America', 'Central Asia', 'N Asia', 'SW Asia', 'S Asia'

var ASSET_FOLDER = 'projects/main-aviary-427701-f4/assets/Research_projects';
var ASSET_PREFIX = 'diag2026_08_';

var TILE_SCALE = 16;
// ===========================================================================

var fua = ee.FeatureCollection("users/Jiayong_Liang/Research_projects/FUA2015_100Mpop");

// Feature properties to carry through, in output order.
var META = ['eFUA_ID', 'eFUA_name', 'Cntry_ISO', 'Cntry_name',
            'FUA_area', 'FUA_p_2015', 'fid_1'];

// The 24 bands Stage 1 writes.
var BANDS = ['exDmg', 'exDmgFP', 'exInunD', 'exDmg_tail', 'exInunD_tail',
             'exDmg_pros', 'exInunD_pros', 'exDmg_prosDn', 'exInunD_prosDn',
             'exInunD_a05', 'exInunD_a20', 'height',
             'dmg10', 'dmg20', 'dmg50', 'dmg100', 'dmg200', 'dmg500',
             'inun10', 'inun20', 'inun50', 'inun100', 'inun200', 'inun500'];

// Explicit schema: metadata, then every band's mean and count.
var SELECTORS = META.slice();
BANDS.forEach(function (b) {
  SELECTORS.push(b + '_mean');
  SELECTORS.push(b + '_count');
});

function queueExport(region) {
  var tag = DATASET + '_' + region.replace(/ /g, '');
  var img = ee.Image(ASSET_FOLDER + '/' + ASSET_PREFIX + tag);

  // The asset footprint is already this region's FUA extent, stored at export
  // time - no country-polygon dissolve, no antimeridian span.
  var col = fua.filterBounds(img.geometry());

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
    fileFormat: 'CSV',
    selectors: SELECTORS          // the fix
  });
  return tag;
}

var queued = REGIONS.map(queueExport);
print('Queued ' + queued.length + ' tasks with an explicit ' +
      SELECTORS.length + '-column schema:', queued);
print('selectors:', SELECTORS);
