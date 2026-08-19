/**
 * STAGE1_diagnostics_toAsset_2026-08.js
 *
 * WHY THIS EXISTS
 *
 * Every version so far ran the whole computation graph inside reduceRegions.
 * The original pipeline never did that. It is TWO-STAGE:
 *
 *   mapExport_Jan2026.js   Export.image.toAsset  -> FloodRiskViewGlobal_Jan26
 *   fuaExport_Jan2026.js   reduceRegions OVER THAT MATERIALISED ASSET
 *
 * That is the structural difference, and it was in the deposited code the whole
 * time. Zonal statistics over a stored asset are cheap - there is no expression
 * tree to evaluate per tile, just pixels to read. Zonal statistics over a live
 * graph re-derive six mosaics, sixty threshold comparisons and the whole
 * trapezoid stack for every tile of every feature, which is what has been
 * exhausting memory on the large sub-regions.
 *
 * Run this script first, wait for the asset, then run
 * STAGE2_diagnostics_fuaExport_2026-08.js.
 *
 * REVISION 2. Comparing the first Stage 2 output against the published values
 * showed FD-AED reproducing them exactly (median new/old ratio 1.000 over 271
 * FUAs) while IR-AED came out at about a third. The cause was a domain
 * mismatch that turned out to exist in the published analysis itself: FD-AED
 * was averaged over the whole modelled floodplain, IR-AED only over pixels
 * carrying a building height - a median of 34% of them. The two were never
 * like-for-like.
 *
 * Every metric is now computed on the built-up floodplain, FD-AED included, so
 * the FD-AED vs IR-AED comparison that the paper rests on is valid. exDmgFP
 * reproduces the published full-floodplain FD-AED for reference.
 *
 * REVISION 3. Revision 2 defined the built-up domain as height.mask(), which
 * selects nothing: GHS_BUILT_H is unmasked over all land and carries 0 where
 * nothing is built. The Auckland test came back with exDmg identical to
 * exDmgFP bit for bit, and a floodplain mean height of 0.80 m against 2.96 m
 * over the layer's own domain - the signature of many zero-height pixels being
 * averaged in. The domain is now height > 0.
 *
 * CONSEQUENCE: FD-AED values from this run will differ from the published ones.
 * That is intended. Regional shares, country tertiles and the figures built on
 * them will need regenerating from the new values.
 *
 * SIZE
 *
 * Bands are masked to the 10-yr floodplain, which on the Oceania test was
 * 10,847 of 274,569 pixels - about 4% of the built-up area. Exporting it region
 * by region rather than globally keeps each asset small and lets you delete
 * each one after its Stage 2 CSV is downloaded. Given the storage pressure that
 * led to the WSF3D and GBH2020 deletions, do not export globally in one go.
 *
 * HOW TO RUN
 *   1. Paste into a new Earth Engine script, Save, Run, then RUN ALL.
 *      One asset export task per region, smallest first.
 *   2. These are IMAGE exports, so they take far longer than the table exports
 *      you have been running - tens of minutes to a couple of hours for the
 *      big regions. They do not need babysitting.
 *   3. Assets appear in ASSET_FOLDER (Assets tab), one per region.
 *   4. As each finishes, add that region to REGIONS in Stage 2 and run it.
 *   5. Delete each Stage 1 asset once its Stage 2 CSV is downloaded.
 *
 * A single mosaic is used for all six return periods here. The original called
 * .mosaic() six times, which was affordable only because it happened once
 * during an image export rather than inside every reduceRegions tile.
 */

// ===========================================================================
// CONFIG
// ===========================================================================
// All regions queued in one Run. Ordered smallest first, so Oceania confirms
// the chain end to end before the expensive ones start.
// Full list, if you ever need the others:
//   Oceania | Australia | Central America | Central Asia | N Asia | SW Asia
//   S Asia  | SE Asia   | South America   | North America | Europe | Africa | E Asia
var REGIONS = ['Oceania', 'South America', 'SE Asia', 'North America',
               'Africa', 'Europe', 'E Asia'];

var DATASET = 'JRC';       // WSF3D / GBH2020 assets have been deleted

var ASSET_FOLDER  = 'projects/main-aviary-427701-f4/assets/Research_projects';
var ASSET_PREFIX  = 'diag2026_08_';

var FLOPROS_LAYER = 'flopros_merge';
var TAIL_RP       = 1000;
// ===========================================================================

// One mosaic for all six return periods, not six separate ones.
var hazard = ee.ImageCollection('JRC/CEMS_GLOFAS/FloodHazard/v2_1').mosaic();
var rp10  = hazard.select('RP10_depth'),
    rp20  = hazard.select('RP20_depth'),
    rp50  = hazard.select('RP50_depth'),
    rp100 = hazard.select('RP100_depth'),
    rp200 = hazard.select('RP200_depth'),
    rp500 = hazard.select('RP500_depth');

var flopros_merge = ee.Image("users/Jiayong_Liang/Research_projects/FLOPROS_merge"),
    flopros_model = ee.Image("users/Jiayong_Liang/Research_projects/FLOPROS_model");

var LSIB_SIMPLE = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017');

function getHeight(heightSource) {
  if (heightSource === 'JRC') {
    return ee.Image("JRC/GHSL/P2023A/GHS_BUILT_H/2018").select('built_height');
  } else if (heightSource === 'WSF3D') {
    // WSF3D V02 is stored in decimetres.
    return ee.Image("projects/ee-knhuang/assets/WSF3D_V02_90m").select(0).divide(10);
  } else if (heightSource === 'GBH2020') {
    return ee.Image("projects/ee-knhuang/assets/GBH2020_150m").select(0);
  }
  throw new Error('heightSource must be "JRC", "WSF3D" or "GBH2020".');
}

var AEP = {rp10: 0.1, rp20: 0.05, rp50: 0.02, rp100: 0.01, rp200: 0.005, rp500: 0.002};

var BANDS = [
  ['500', '200', AEP.rp200 - AEP.rp500],   // 0.003
  ['200', '100', AEP.rp100 - AEP.rp200],   // 0.005
  ['100', '50',  AEP.rp50  - AEP.rp100],   // 0.010
  ['50',  '20',  AEP.rp20  - AEP.rp50],    // 0.030
  ['20',  '10',  AEP.rp10  - AEP.rp20]     // 0.050
];

var DAMAGE_THRESHOLDS = {
  Europe:    [0.2, 0.6, 0.9, 1.2, 1.8, 2.2, 2.8, 3.4, 4.2, 5.5],
  NAmerica:  [0.1, 0.25, 0.4, 0.65, 1, 1.5, 2, 3, 4, 6],
  CSAmerica: [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.8, 1, 1.5, 3],
  Asia:      [0.1, 0.2, 0.4, 0.8, 1, 1.4, 1.8, 2.5, 3.6, 5.5],
  Africa:    [0.4, 0.7, 1, 1.4, 1.6, 2.2, 2.8, 3.2, 4, 5.5],
  Oceania:   [0.2, 0.3, 0.4, 0.6, 0.8, 1.2, 1.5, 1.9, 2.6, 5]
};

var CURVE_OF = {
  'Oceania': 'Oceania', 'Australia': 'Oceania',
  'Central America': 'CSAmerica', 'South America': 'CSAmerica',
  'North America': 'NAmerica', 'Europe': 'Europe', 'Africa': 'Africa',
  'E Asia': 'Asia', 'S Asia': 'Asia', 'SE Asia': 'Asia',
  'SW Asia': 'Asia', 'N Asia': 'Asia', 'Central Asia': 'Asia'
};

// Bands surviving under each protection bin (binIdx 0..6).
var SURVIVING_UP   = [5, 4, 3, 2, 1, 0, -1];
var SURVIVING_DOWN = [5, 5, 4, 3, 2, 1,  0];

// ---------------------------------------------------------------------------
function diagnosticsImage(heightSource, curveName) {

  var height = getHeight(heightSource);
  var thresholds = DAMAGE_THRESHOLDS[curveName];

  // Unmask so pixels with no protection record count as unprotected rather
  // than being dropped.
  var protectYear = ((FLOPROS_LAYER === 'flopros_model') ? flopros_model
                                                         : flopros_merge).unmask(0);

  // TWO DOMAINS, and the distinction is the point of this revision.
  //
  //   domainFP = rp10 coverage.               The full modelled floodplain.
  //                                           What published FD-AED used.
  //   domainBU = rp10 coverage AND height>0.  The built-up floodplain - pixels
  //                                           that actually contain buildings.
  //
  // NOTE the height>0 test rather than height.mask(). GHS_BUILT_H is unmasked
  // over all land and simply carries 0 where nothing is built, so masking by
  // height.mask() selects nothing: revision 2 of this script produced
  // exDmg identical to exDmgFP, bit for bit, on the Auckland test. Only a
  // value test isolates the built-up floodplain.
  //
  // The published analysis compared an FD-AED averaged over domainFP against an
  // IR-AED averaged over domainBU, so the two were never like-for-like. Every
  // metric here is therefore computed on domainBU, including FD-AED, making the
  // comparison valid. exDmgFP is carried alongside purely to reproduce the
  // published FD-AED and quantify what restricting the domain changes.
  //
  // Intersecting masks across projections is affordable here because this is a
  // one-off image export. It is what made reduceRegions run out of memory when
  // the same intersection sat inside a live computation.
  var domainFP = rp10.mask();
  var domainBU = rp10.mask().and(height.gt(0));

  var depths = {'10': rp10, '20': rp20, '50': rp50,
                '100': rp100, '200': rp200, '500': rp500};

  function damageOf(d) {
    var acc = ee.Image(0);
    for (var i = 0; i < thresholds.length; i++) {
      acc = acc.add(d.gt(thresholds[i]));
    }
    return acc.divide(thresholds.length);
  }

  var dmg = {}, dmgFP = {}, inun = {}, a05 = {}, a20 = {};
  Object.keys(depths).forEach(function (rp) {
    var d = depths[rp];
    // damageOf is evaluated once and masked two ways.
    var dRaw = damageOf(d);
    dmg[rp]   = dRaw.updateMask(domainBU).rename('dmg' + rp);
    dmgFP[rp] = dRaw.updateMask(domainFP);
    var capped = d.divide(height).min(1).updateMask(domainBU).rename('inun' + rp);
    inun[rp] = capped;
    a05[rp] = capped.pow(0.5);
    a20[rp] = capped.pow(2.0);
  });

  function cumulative(perRP) {
    var cum = [ee.Image(0)];
    var running = ee.Image(0);
    for (var i = 0; i < BANDS.length; i++) {
      var r = BANDS[i][0], f = BANDS[i][1], dp = BANDS[i][2];
      running = running.add(perRP[r].add(perRP[f]).multiply(dp).divide(2));
      cum.push(running);
    }
    return cum;
  }
  function tailTerm(perRP, tailRP) { return perRP['500'].multiply(1.0 / tailRP); }

  var cumDmg = cumulative(dmg), cumInun = cumulative(inun);

  var binIdx = ee.Image(0)
    .where(protectYear.gte(10),  1)
    .where(protectYear.gte(20),  2)
    .where(protectYear.gte(50),  3)
    .where(protectYear.gte(100), 4)
    .where(protectYear.gte(200), 5)
    .where(protectYear.gte(500), 6);

  function assembleProtected(cum, perRP, surviving) {
    var tail500 = tailTerm(perRP, 500);
    var tailRP  = tailTerm(perRP, TAIL_RP);
    var out = cum[surviving[0]].add(tail500);
    for (var k = 1; k < surviving.length; k++) {
      var n = surviving[k];
      var residual = (n < 0) ? tailRP : cum[n].add(tail500);
      out = out.where(binIdx.eq(k), residual);
    }
    return out;
  }

  var parts = [
    cumDmg[5].rename('exDmg'),
    cumInun[5].rename('exInunD'),
    cumDmg[5].add(tailTerm(dmg, 500)).rename('exDmg_tail'),
    cumInun[5].add(tailTerm(inun, 500)).rename('exInunD_tail'),
    assembleProtected(cumDmg,  dmg,  SURVIVING_UP).rename('exDmg_pros'),
    assembleProtected(cumInun, inun, SURVIVING_UP).rename('exInunD_pros'),
    assembleProtected(cumDmg,  dmg,  SURVIVING_DOWN).rename('exDmg_prosDn'),
    assembleProtected(cumInun, inun, SURVIVING_DOWN).rename('exInunD_prosDn'),
    cumulative(a05)[5].rename('exInunD_a05'),
    cumulative(a20)[5].rename('exInunD_a20'),
    // Published FD-AED, on the full floodplain. Not used in any comparison with
    // IR-AED - it is here so the run can be checked against the published
    // numbers and so the effect of restricting the domain can be quantified.
    cumulative(dmgFP)[5].rename('exDmgFP'),
    // On the built-up domain, matching how the published mean heights were
    // computed.
    height.updateMask(domainBU).rename('height')
  ];
  Object.keys(depths).forEach(function (rp) {
    parts.push(dmg[rp]);
    parts.push(inun[rp]);
  });

  // No blanket mask here: each band already carries its domain, and domainBU is
  // a subset of domainFP, so the stored asset stays sparse.
  return ee.Image.cat(parts).toFloat();
}

// ---------------------------------------------------------------------------
var fua = ee.FeatureCollection("users/Jiayong_Liang/Research_projects/FUA2015_100Mpop");

function queueAsset(region) {
  var tag = DATASET + '_' + region.replace(/ /g, '');
  var regionCol = LSIB_SIMPLE.filter(ee.Filter.eq('wld_rgn', region));

  // Export only where the FUAs are, not the whole continent. Using the FUA
  // union as the export region rather than its bounding box keeps North
  // America from spanning Alaska to Panama, and cuts the exported area to a
  // small fraction of the land surface.
  var exportRegion = fua.filterBounds(regionCol.geometry(1000)).geometry(1000);

  Export.image.toAsset({
    image: diagnosticsImage(DATASET, CURVE_OF[region]).clip(exportRegion),
    description: 'STAGE1_' + tag,
    assetId: ASSET_FOLDER + '/' + ASSET_PREFIX + tag,
    region: exportRegion,
    scale: 100,
    maxPixels: 1e13,
    pyramidingPolicy: {'.default': 'mean'}
  });
  return ASSET_PREFIX + tag;
}

var queued = REGIONS.map(queueAsset);
print('Queued ' + queued.length + ' asset exports in ' + ASSET_FOLDER + ':', queued);
print('Bands (24 expected):',
      diagnosticsImage(DATASET, CURVE_OF[REGIONS[0]]).bandNames());
