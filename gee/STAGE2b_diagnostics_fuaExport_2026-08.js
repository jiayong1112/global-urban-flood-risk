/**
 * STAGE2b_diagnostics_fuaExport_2026-08.js
 *
 * For the four regions Stage 2 could not finish: E Asia, Europe, North America,
 * Africa. Oceania, SE Asia and South America already succeeded - keep those
 * CSVs and do not re-run them.
 *
 * WHY STAGE 2 FAILED AT ALL
 *
 * Reducing over a materialised asset should be cheap, and for three regions it
 * was. The tell is Europe: it died after only 216 EECU-seconds, far too early
 * for the pixel work to be the problem. The cost was in selecting the features,
 * not in reducing them:
 *
 *     fua.filterBounds(regionCol.geometry(1000))
 *
 * regionCol.geometry(1000) dissolves every LSIB country polygon in the region
 * into one multipolygon at request time. Europe has ~40 countries and Africa
 * ~50, all with detailed coastlines. That dissolve is expensive and happens
 * before a single pixel is read.
 *
 * North America has a second, worse version of the same problem: LSIB North
 * America includes Alaska, so the dissolved geometry straddles the antimeridian
 * and spans essentially the whole globe in longitude. filterBounds against it
 * selects far more FUAs than the region contains.
 *
 * THE FIX
 *
 * Use the Stage 1 asset's own footprint instead. Stage 1 clipped each asset to
 * the union of that region's FUAs, so the footprint already IS the region's FUA
 * extent - stored, not recomputed, and free of the Alaska problem:
 *
 *     var col = fua.filterBounds(img.geometry());
 *
 * TILE_SCALE also goes 4 -> 16, and chunking and band-group options are here if
 * a region still needs them. Neither should be necessary.
 *
 * HOW TO RUN
 *   1. Paste into a NEW Earth Engine script, Save, Run, then RUN ALL.
 *   2. Download into
 *        revision-2026-08/analysis/csv_fua_diag_2026-08/
 *      alongside the three CSVs that already succeeded, then run
 *        python a3_integration_diagnostics.py
 *
 * Output file names match Stage 2 exactly, so the Python merge is unchanged.
 */

// ===========================================================================
// CONFIG
// ===========================================================================
var DATASET = 'JRC';

// Only the regions that failed. The other three are done.
var REGIONS = ['Europe', 'North America', 'Africa', 'E Asia'];

var ASSET_FOLDER = 'projects/main-aviary-427701-f4/assets/Research_projects';
var ASSET_PREFIX = 'diag2026_08_';

var TILE_SCALE   = 16;     // Earth Engine maximum
var MEAN_ONLY    = false;  // true drops the _count columns, halving output width
var BAND_GROUP   = 'all';  // 'all' | 'core' | 'perRP'  - split only if needed
var CHUNKS       = {};     // e.g. {'E Asia': 2} to split a region across tasks
// ===========================================================================

var fua = ee.FeatureCollection("users/Jiayong_Liang/Research_projects/FUA2015_100Mpop");

var CORE_BANDS = ['exDmg', 'exDmgFP', 'exInunD', 'exDmg_tail', 'exInunD_tail',
                  'exDmg_pros', 'exInunD_pros', 'exDmg_prosDn', 'exInunD_prosDn',
                  'exInunD_a05', 'exInunD_a20', 'height'];
var PERRP_BANDS = ['dmg10', 'dmg20', 'dmg50', 'dmg100', 'dmg200', 'dmg500',
                   'inun10', 'inun20', 'inun50', 'inun100', 'inun200', 'inun500'];

/** Deterministic modulo split, no getInfo required. */
function chunkOf(col, k, n) {
  if (n <= 1) { return col; }
  return col.map(function (f) {
    return f.set('_chunk', ee.Number(f.get('eFUA_ID')).toInt().mod(n));
  }).filter(ee.Filter.eq('_chunk', k));
}

function queueExport(region, k, n) {
  var tag = DATASET + '_' + region.replace(/ /g, '');
  var img = ee.Image(ASSET_FOLDER + '/' + ASSET_PREFIX + tag);

  if (BAND_GROUP === 'core')  { img = img.select(CORE_BANDS); }
  if (BAND_GROUP === 'perRP') { img = img.select(PERRP_BANDS); }

  // The asset footprint is already the union of this region's FUAs, computed
  // once at export time. No country-polygon dissolve, and no antimeridian span.
  var col = chunkOf(fua.filterBounds(img.geometry()), k, n);

  var reducer = MEAN_ONLY
    ? ee.Reducer.mean()
    : ee.Reducer.mean().combine({reducer2: ee.Reducer.count(), sharedInputs: true});

  var stats = img.reduceRegions({
    collection: col,
    reducer: reducer,
    scale: 100,
    tileScale: TILE_SCALE
  }).map(function (ft) { return ft.setGeometry(null); });

  var name = tag + (BAND_GROUP === 'all' ? '' : '_' + BAND_GROUP) +
             (n > 1 ? '_c' + k : '');
  Export.table.toDrive({
    collection: stats,
    folder: 'csv_fua_diag_2026-08',
    description: name + '_diag_2026-08',
    fileFormat: 'CSV'
  });
  return name;
}

var queued = [];
REGIONS.forEach(function (region) {
  var n = CHUNKS[region] || 1;
  for (var k = 0; k < n; k++) { queued.push(queueExport(region, k, n)); }
});

print('Queued ' + queued.length + ' zonal-statistics tasks:', queued);

// Sanity check: how many FUAs each asset footprint selects. If North America
// comes back with far more than ~61, the antimeridian problem is still present.
REGIONS.forEach(function (region) {
  var tag = DATASET + '_' + region.replace(/ /g, '');
  var img = ee.Image(ASSET_FOLDER + '/' + ASSET_PREFIX + tag);
  print(region + ' FUAs selected by asset footprint:',
        fua.filterBounds(img.geometry()).size());
});
