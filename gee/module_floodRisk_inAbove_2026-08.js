/**
 * module_floodRisk_inAbove_2026-08.js
 *
 * Core pixel-level flood-risk module. Supersedes
 * module_floodRisk_inAbove_Jan2026.js. The depth-damage functions, the
 * inundation ratio, the trapezoidal integration weights and the mapping from a
 * FLOPROS standard to the surviving probability bands are all unchanged, so
 * every quantity reproduces the earlier module except where listed below.
 *
 * THREE CHANGES
 *
 * 1. The rare-event tail is integrated over the same probability range for the
 *    protected and the unprotected metrics.
 *
 *    Previously the rectangular tail term D(d500) x p was added only to the two
 *    rarest protection bins (pros500 used p = 1/500, pros500Plus used p = 1/1000)
 *    and to neither the other protection bins nor the unprotected metrics. The
 *    two families were therefore integrated over slightly different probability
 *    ranges, and a small number of urban areas returned a protected annual
 *    expected damage marginally above the unprotected value, which is not
 *    physically possible.
 *
 *    Now every metric carries the tail: the unprotected metrics and protection
 *    bins 0-5 use TAIL_P = 1/500, and the T >= 500 yr bin uses TAIL_P_500PLUS =
 *    1/1000. Because the surviving bands are a subset of all bands and every
 *    term is non-negative, the protected value is now bounded above by the
 *    unprotected value at every pixel.
 *
 * 2. Pixels with no FLOPROS record are masked out rather than assumed
 *    unprotected. protectYear.selfMask() is retained for the protected metrics,
 *    and the same mask is applied to a matching pair of unprotected bands
 *    (exDmg_cmp, exInunD_cmp) so that the protected and unprotected metrics
 *    being compared are averaged over exactly the same pixels. Without that,
 *    the monotonicity in (1) holds pixel by pixel but not necessarily after
 *    spatial averaging.
 *
 * 3. Building height is exported on two explicit domains:
 *      height     - the FUA-wide mean, over settlement pixels across the whole
 *                   analysis unit. This is the statistic reported in the text.
 *      height_fp  - the mean over the built-up floodplain, i.e. exactly the
 *                   pixels where the inundation ratio is evaluated.
 *    The two differ substantially (floodplain buildings are lower than the city
 *    average), and reporting both removes the ambiguity in the earlier output,
 *    which carried only the first while the metric used the second.
 *
 * DOMAINS. FD-AED is averaged over the modelled floodplain; IR-AED requires a
 * building height in its denominator and is averaged over the built-up part of
 * that floodplain. Both are retained, and the Methods state the difference.
 *
 * Usage:
 *   var mod = require('users/<you>/<repo>:module_floodRisk_inAbove_2026-08');
 *   var img = mod.expected_annual_flood_risk_fullOut('flopros_merge', 'Asia');
 */

// ---------------------------------------------------------------- inputs ---
var hazardCol = ee.ImageCollection('JRC/CEMS_GLOFAS/FloodHazard/v2_1').mosaic();
var RP = ['10', '20', '50', '100', '200', '500'];
var depth = {};
RP.forEach(function (rp) { depth[rp] = hazardCol.select('RP' + rp + '_depth'); });

var HEIGHT_SOURCE = 'JRC';          // 'JRC' | 'WSF3D' | 'GBH2020'

function getHeight(src) {
  if (src === 'JRC') {
    return ee.Image('JRC/GHSL/P2023A/GHS_BUILT_H/2018').select('built_height');
  }
  if (src === 'WSF3D') {
    // WSF3D V02 stores height in decimetres; convert to metres before use.
    return ee.Image('projects/ee-knhuang/assets/WSF3D_V02_90m').select(0).divide(10);
  }
  if (src === 'GBH2020') {
    return ee.Image('projects/ee-knhuang/assets/GBH2020_150m').select(0);
  }
  throw new Error('HEIGHT_SOURCE must be JRC, WSF3D or GBH2020');
}

var flopros = {
  flopros_merge: ee.Image('users/Jiayong_Liang/Research_projects/FLOPROS_merge'),
  flopros_model: ee.Image('users/Jiayong_Liang/Research_projects/FLOPROS_model')
};

// Decile thresholds of the regional Huizinga (2017) depth-damage curves.
var DAMAGE_THRESHOLDS = {
  Europe:    [0.2, 0.6, 0.9, 1.2, 1.8, 2.2, 2.8, 3.4, 4.2, 5.5],
  NAmerica:  [0.1, 0.25, 0.4, 0.65, 1, 1.5, 2, 3, 4, 6],
  CSAmerica: [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.8, 1, 1.5, 3],
  Asia:      [0.1, 0.2, 0.4, 0.8, 1, 1.4, 1.8, 2.5, 3.6, 5.5],
  Africa:    [0.4, 0.7, 1, 1.4, 1.6, 2.2, 2.8, 3.2, 4, 5.5],
  Oceania:   [0.2, 0.3, 0.4, 0.6, 0.8, 1.2, 1.5, 1.9, 2.6, 5]
};

// Trapezoid bands, rarest first: [rarer RP, more frequent RP, delta p].
var BANDS = [['500', '200', 0.003], ['200', '100', 0.005], ['100', '50', 0.010],
             ['50', '20', 0.030], ['20', '10', 0.050]];

// Rare-event tail, now applied to protected and unprotected alike.
var TAIL_P = 1 / 500;
var TAIL_P_500PLUS = 1 / 1000;

// Bands surviving under each FLOPROS bin, counting from the rarest.
// bin 0: T < 10   1: 10-20   2: 20-50   3: 50-100   4: 100-200   5: 200-500   6: >= 500
var SURVIVING = [5, 4, 3, 2, 1, 0, 0];

// ---------------------------------------------------------------- helpers --
function damageOf(d, curve) {
  return d.gt(ee.Image(DAMAGE_THRESHOLDS[curve])).reduce('sum').divide(10);
}

function cumulative(perRP) {
  // cum[n] = trapezoid sum over the n rarest bands.
  var cum = [ee.Image(0)];
  var running = ee.Image(0);
  BANDS.forEach(function (b) {
    running = running.add(perRP[b[0]].add(perRP[b[1]]).multiply(b[2]).divide(2));
    cum.push(running);
  });
  return cum;
}

// ---------------------------------------------------------------- main -----
/**
 * @param {string} floprosLayer  'flopros_merge' | 'flopros_model'
 * @param {string} curve         'Europe'|'NAmerica'|'CSAmerica'|'Asia'|'Africa'|'Oceania'
 * @return {ee.Image} multi-band pixel-level risk image
 */
exports.expected_annual_flood_risk_fullOut = function (floprosLayer, curve) {
  if (!DAMAGE_THRESHOLDS[curve]) throw new Error('unknown curve: ' + curve);
  var height = getHeight(HEIGHT_SOURCE);
  var protectYear = flopros[floprosLayer];
  if (!protectYear) throw new Error('unknown FLOPROS layer: ' + floprosLayer);

  // Two averaging domains, both retained and both reported.
  //   domainFP = modelled floodplain                 -> FD-AED
  //   domainBU = floodplain AND a building present   -> IR-AED
  // GHS_BUILT_H is unmasked over land and carries 0 where nothing is built, so
  // the built-up test must be a value test, not height.mask().
  var domainFP = depth['10'].mask();
  var domainBU = domainFP.and(height.gt(0));

  // Pixels carrying an actual FLOPROS record. Where none exists we do not know
  // the standard, so those pixels are excluded rather than assumed unprotected.
  var floprosValid = protectYear.selfMask().mask();

  var dmg = {}, inun = {};
  RP.forEach(function (rp) {
    var d = depth[rp];
    dmg[rp] = damageOf(d, curve).updateMask(domainFP);
    inun[rp] = d.divide(height).min(1).updateMask(domainBU);
  });

  var cumDmg = cumulative(dmg);
  var cumInun = cumulative(inun);
  var tailDmg = dmg['500'].multiply(TAIL_P);
  var tailInun = inun['500'].multiply(TAIL_P);
  var tailDmg500Plus = dmg['500'].multiply(TAIL_P_500PLUS);
  var tailInun500Plus = inun['500'].multiply(TAIL_P_500PLUS);

  // Unprotected: every band plus the tail.
  var exDmg = cumDmg[5].add(tailDmg).rename('exDmg');
  var exInunD = cumInun[5].add(tailInun).rename('exInunD');

  var binIdx = ee.Image(0)
    .where(protectYear.gte(10), 1)
    .where(protectYear.gte(20), 2)
    .where(protectYear.gte(50), 3)
    .where(protectYear.gte(100), 4)
    .where(protectYear.gte(200), 5)
    .where(protectYear.gte(500), 6);

  function assembleProtected(cum, tail, tail500Plus) {
    var out = cum[SURVIVING[0]].add(tail);
    for (var k = 1; k < SURVIVING.length; k++) {
      var residual = (k === 6) ? tail500Plus : cum[SURVIVING[k]].add(tail);
      out = out.where(binIdx.eq(k), residual);
    }
    return out.updateMask(floprosValid);
  }

  var exDmgPros = assembleProtected(cumDmg, tailDmg, tailDmg500Plus).rename('exDmg_pros');
  var exInunDPros = assembleProtected(cumInun, tailInun, tailInun500Plus).rename('exInunD_pros');

  // Like-for-like partners: the unprotected metrics on the same pixels as the
  // protected ones, so that a mean over any region satisfies pros <= unprotected.
  var exDmgCmp = exDmg.updateMask(floprosValid).rename('exDmg_cmp');
  var exInunDCmp = exInunD.updateMask(floprosValid).rename('exInunD_cmp');

  var exDep = cumulative(
    (function () { var o = {}; RP.forEach(function (rp) { o[rp] = depth[rp].updateMask(domainFP); }); return o; })()
  )[5].rename('exDep');

  return exDep
    .addBands(exDmg).addBands(exInunD)
    .addBands(exDmgPros).addBands(exInunDPros)
    .addBands(exDmgCmp).addBands(exInunDCmp)
    // height on both domains: FUA-wide (reported in the text) and built-up
    // floodplain (the pixels the inundation ratio actually uses)
    .addBands(height.selfMask().rename('height'))
    .addBands(height.updateMask(domainBU).rename('height_fp'))
    .addBands(protectYear.selfMask().rename('flopros'));
};

exports.RP = RP;
exports.BANDS = BANDS;
exports.TAIL_P = TAIL_P;
exports.DAMAGE_THRESHOLDS = DAMAGE_THRESHOLDS;
