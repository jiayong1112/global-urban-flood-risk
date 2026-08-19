/**
 * STAGE2c_1b_diagnostics_fuaExport_2026-08.js
 *
 * Zonal statistics for the six sub-regions built by
 * STAGE1b_diagnostics_toAsset_2026-08.js:
 *
 *     SAsia 123 | SWAsia 42 | CAmerica 11 | CAsia 6 | Australia 5
 *     EuropeExtra 1 (Denmark) | AfricaExtra 1 (Somalia)
 *
 * 189 cities in total, S Asia being the largest. Job names, not LSIB region
 * names: Stage 1b revision 2 selects by explicit country list.
 *
 * IDENTICAL to STAGE2c_diagnostics_fuaExport_2026-08.js apart from the REGIONS
 * list. Generated from it by substitution, not retyped.
 *
 * WHY THIS USES AN EXPLICIT SCHEMA - it matters more here than anywhere else.
 * Export.table.toDrive infers CSV columns from the FIRST feature, and a city
 * with zero contributing pixels sets no mean properties. When that city sorts
 * first, every _mean column vanishes for the whole table. It already happened
 * twice: Europe (Yerevan, 0 px) and North America (Port-au-Prince, 0 px) both
 * exported counts only. Central America and Australia are small regions whose
 * first city may well be dry, so the `selectors` list below is not optional.
 *
 * HOW TO RUN
 *   1. Wait for the Stage 1b assets to appear in ASSET_FOLDER. A region whose
 *      asset is not ready yet fails with "Image not found" - run those later
 *      rather than all at once if the exports are still going.
 *   2. Paste into a new Earth Engine script, Save, Run, then RUN ALL.
 *   3. Download into revision-2026-08/analysis/csv_fua_diag_2026-08/ alongside
 *      the seven regions already there, then run
 *        python a3_integration_diagnostics.py
 *      That should take coverage from 467 to roughly 633 cities.
 *   4. Delete each Stage 1b asset once its CSV is downloaded.
 *
 * Output names match the other stages, so the Python merge is unchanged. Cities
 * picked up twice through footprint overlap are resolved to the row with the
 * most contributing pixels.
 */

// ===========================================================================
// CONFIG
// ===========================================================================
var DATASET = 'JRC';

// The seven Stage 1b jobs. These are JOB names, not LSIB region names -
// Stage 1b selects by explicit country list, so the assets are named
// diag2026_08_JRC_<job>.
// Already done - do not re-run: Oceania, South America, SE Asia, North America,
// Africa, Europe, E Asia.
var REGIONS = ['EuropeExtra', 'AfricaExtra', 'Australia', 'CAsia',
               'CAmerica', 'SWAsia', 'SAsia'];

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
