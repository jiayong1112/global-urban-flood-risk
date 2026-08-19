/**
 * fuaExport_2026-08.js
 *
 * Per-FUA export of the pixel-level risk image produced by
 * module_floodRisk_inAbove_2026-08.js.
 *
 * WHY THIS REPLACES fuaExport_Jan2026.js
 *
 * The earlier script selected FUAs with
 *     fua.filterBounds(LSIB.filter(wld_rgn == region).geometry())
 * which dissolves every country polygon in an LSIB world region at request
 * time. That is slow, and it silently returns the wrong set when the dissolved
 * geometry is large or straddles the antimeridian. The North America batch of
 * the January export returned only 6 of Mexico's 14 FUAs: Mexico City,
 * Guadalajara, Puebla, Toluca, Leon, Queretaro, Aguascalientes and Cuernavaca
 * are absent from csv_fua_2026-1-17/JRC_NAmerica_FloodRisk.csv, although they
 * are present in the country-level table.
 *
 * This script selects FUAs by the FUA layer's own Cntry_name property. Nothing
 * is dissolved, no geometry can straddle the dateline, and the country lists are
 * explicit, so the exported set can be checked against Table S2 of the paper.
 *
 * HOW TO RUN
 *   1. Paste into the Earth Engine Code Editor and Save.
 *   2. Set BATCH below and Run. READ THE CONSOLE FIRST: it prints the number of
 *      FUAs selected and the countries found. If a count is far larger than
 *      expected, stop - the selection is wrong.
 *   3. Then run the export task. Batches are sized to finish individually;
 *      'Mexico' alone is the quick one to verify the chain end to end.
 *   4. Download the CSVs to  revision-2026-08/analysis/csv_fua_2026-08/
 *
 * OUTPUT COLUMNS (per FUA, mean / count / sum for each band)
 *   exDmg, exInunD              unprotected FD-AED and IR-AED, tail included
 *   exDmg_pros, exInunD_pros    after protection, tail included, FLOPROS pixels
 *   exDmg_cmp, exInunD_cmp      unprotected on the FLOPROS pixels only, the
 *                               like-for-like partner of the protected columns
 *   height                      FUA-wide mean building height
 *   height_fp                   mean building height on the built-up floodplain
 *   flopros                     mean protection standard (years)
 */

var mod = require('users/Jiayong_Liang/public:module_floodRisk_inAbove_2026-08');

var fua = ee.FeatureCollection('users/Jiayong_Liang/Research_projects/FUA2015_100Mpop');

// ===========================================================================
// CONFIG
// ===========================================================================
var BATCH = 'Mexico';           // see BATCHES below
var FLOPROS_LAYER = 'flopros_merge';
var SCALE = 100;
var DRIVE_FOLDER = 'flood_fua_2026_08';
// ===========================================================================

// Country -> depth-damage curve. Matches Table S2 of the manuscript.
var CURVE_OF = {
  Europe: ['Austria', 'Belarus', 'Belgium', 'Bulgaria', 'Croatia', 'CzechRepublic',
           'Denmark', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Ireland',
           'Italy', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'Romania', 'Russia',
           'Serbia', 'Slovakia', 'Spain', 'Sweden', 'Switzerland', 'Ukraine',
           'UnitedKingdom', 'UnitedKingdom(Scotland)'],
  NAmerica: ['Canada', 'Mexico', 'UnitedStates'],
  CSAmerica: ['Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'CostaRica',
              'DominicanRepublic', 'Ecuador', 'ElSalvador', 'Guatemala', 'Honduras',
              'Nicaragua', 'Panama', 'Paraguay', 'Peru', 'Uruguay', 'Venezuela'],
  Asia: ['Afghanistan', 'Armenia', 'Azerbaijan', 'Bahrain', 'Bangladesh', 'Cambodia',
         'China', 'Georgia', 'HongKong', 'India', 'Indonesia', 'Iran', 'Iraq', 'Israel',
         'Japan', 'Jordan', 'Kazakhstan', 'Kuwait', 'Kyrgyzstan', 'Lebanon', 'Malaysia',
         'Mongolia', 'Myanmar', 'Nepal', 'NorthKorea', 'Pakistan', 'Palestina',
         'Philippines', 'Qatar', 'SaudiArabia', 'Singapore', 'SouthKorea', 'SriLanka',
         'Syria', 'Taiwan', 'Tajikistan', 'Thailand', 'Turkey', 'UnitedArabEmirates',
         'Uzbekistan', 'Vietnam', 'Yemen'],
  Africa: ['Algeria', 'Angola', 'Benin', 'BurkinaFaso', 'Cameroon',
           'CentralAfricanRepublic', 'Chad', 'CotedIvoire',
           'DemocraticRepublicoftheCongo', 'Egypt', 'Ethiopia', 'Ghana', 'Guinea',
           'Kenya', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania',
           'Morocco', 'Mozambique', 'Niger', 'Nigeria', 'RepublicofCongo', 'Rwanda',
           'Senegal', 'SierraLeone', 'Somalia', 'SouthAfrica', 'Sudan', 'Tanzania',
           'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe'],
  Oceania: ['Australia', 'NewZealand']
};

// Export batches. Each batch names one curve, because the depth-damage function
// is regional and one image can carry only one curve.
var BATCHES = {
  // the gap-fill batch: run this one first
  'Mexico':        {curve: 'NAmerica', countries: ['Mexico']},
  // full re-run, one batch per curve
  'NAmerica':      {curve: 'NAmerica', countries: CURVE_OF.NAmerica},
  'CSAmerica':     {curve: 'CSAmerica', countries: CURVE_OF.CSAmerica},
  'Europe':        {curve: 'Europe', countries: CURVE_OF.Europe},
  'Africa':        {curve: 'Africa', countries: CURVE_OF.Africa},
  'Oceania':       {curve: 'Oceania', countries: CURVE_OF.Oceania},
  // Asia is the large one; split so each task finishes on its own
  'Asia_China':    {curve: 'Asia', countries: ['China']},
  'Asia_SouthAsia': {curve: 'Asia', countries: ['Afghanistan', 'Bangladesh', 'India',
                                                'Nepal', 'Pakistan', 'SriLanka']},
  'Asia_Rest':     {curve: 'Asia', countries: CURVE_OF.Asia.filter(function (c) {
                      return ['China', 'Afghanistan', 'Bangladesh', 'India', 'Nepal',
                              'Pakistan', 'SriLanka'].indexOf(c) === -1;
                    })}
};

var job = BATCHES[BATCH];
if (!job) throw new Error('unknown BATCH: ' + BATCH);

var selected = fua.filter(ee.Filter.inList('Cntry_name', job.countries));

print('BATCH: ' + BATCH + '  (curve: ' + job.curve + ')');
print('FUAs selected:', selected.size());
print('countries found:', selected.aggregate_array('Cntry_name').distinct().sort());
print('FUA names:', selected.aggregate_array('eFUA_name').sort());

var riskImg = mod.expected_annual_flood_risk_fullOut(FLOPROS_LAYER, job.curve);

var reducers = ee.Reducer.mean()
  .combine({reducer2: ee.Reducer.count(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.sum(), sharedInputs: true});

var stats = riskImg.reduceRegions({
  collection: selected,
  reducer: reducers,
  scale: SCALE,
  tileScale: 4
});

Export.table.toDrive({
  collection: stats.map(function (f) { return f.setGeometry(null); }),
  description: 'JRC_' + BATCH + '_fua_2026-08',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

// Quick visual check that the selection is where you expect it to be.
Map.addLayer(selected, {color: 'red'}, 'selected FUAs (' + BATCH + ')');
Map.centerObject(selected, 4);
