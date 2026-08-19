/**
 * fuaExport_GDP_2026-08.js
 *
 * GDP-weighted per-FUA export: the same four indicators as fuaExport_2026-08.js,
 * each multiplied by gridded total GDP before reduction, so the summed columns
 * are expected annual losses in US$. These are the numerator of Figure 1 panels
 * (b) and (c); the denominator is total GDP per FUA from
 * totalGDP_fuaExport_Jul2026.js.
 *
 * Supersedes fuaExport_GDP_Jan2026.js, for the same two reasons as the
 * unweighted export:
 *   - it uses module_floodRisk_inAbove_2026-08.js, so the rare-event tail is
 *     integrated over the same probability range for the protected and
 *     unprotected metrics, and pixels with no FLOPROS record are masked out
 *     rather than assumed unprotected;
 *   - it selects FUAs by country name rather than by a dissolved LSIB region
 *     geometry. The January GDP export is missing the same 9 FUAs as the
 *     unweighted one: 8 Mexican FUAs including Mexico City, plus Santo Domingo.
 *
 * Run the batches in the same order as fuaExport_2026-08.js and download to
 *   revision-2026-08/analysis/flood_fua_GDP_2026-08/
 *
 * OUTPUT COLUMNS (per FUA; use the _sum columns, which are US$ per year)
 *   exDmg_sum, exInunD_sum              unprotected expected annual loss
 *   exDmg_pros_sum, exInunD_pros_sum    after protection
 *   exDmg_cmp_sum, exInunD_cmp_sum      unprotected on the FLOPROS pixels only
 */

var mod = require('users/Jiayong_Liang/public:module_floodRisk_inAbove_2026-08');

var fua = ee.FeatureCollection('users/Jiayong_Liang/Research_projects/FUA2015_100Mpop');

// Gridded total GDP: GDP per capita (PPP) x population, as in the January export.
var gdp_adm2 = ee.Image('projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022');
var pop2020 = ee.Image('JRC/GHSL/P2023A/GHS_POP/2020');
var totalGDP = gdp_adm2.select('PPP_2022').multiply(pop2020);

// ===========================================================================
// CONFIG - keep BATCH in step with fuaExport_2026-08.js
// ===========================================================================
var BATCH = 'Mexico';
var FLOPROS_LAYER = 'flopros_merge';
var SCALE = 100;
var DRIVE_FOLDER = 'flood_fua_GDP_2026_08';
// ===========================================================================

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

var BATCHES = {
  'Mexico':         {curve: 'NAmerica', countries: ['Mexico']},
  'NAmerica':       {curve: 'NAmerica', countries: CURVE_OF.NAmerica},
  'CSAmerica':      {curve: 'CSAmerica', countries: CURVE_OF.CSAmerica},
  'Europe':         {curve: 'Europe', countries: CURVE_OF.Europe},
  'Africa':         {curve: 'Africa', countries: CURVE_OF.Africa},
  'Oceania':        {curve: 'Oceania', countries: CURVE_OF.Oceania},
  'Asia_China':     {curve: 'Asia', countries: ['China']},
  'Asia_SouthAsia': {curve: 'Asia', countries: ['Afghanistan', 'Bangladesh', 'India',
                                                'Nepal', 'Pakistan', 'SriLanka']},
  'Asia_Rest':      {curve: 'Asia', countries: CURVE_OF.Asia.filter(function (c) {
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

var riskImg = mod.expected_annual_flood_risk_fullOut(FLOPROS_LAYER, job.curve)
  .select(['exDmg', 'exDmg_pros', 'exDmg_cmp',
           'exInunD', 'exInunD_pros', 'exInunD_cmp'])
  .multiply(totalGDP);

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
  description: 'JRC_' + BATCH + '_GDP_fua_2026-08',
  folder: DRIVE_FOLDER,
  fileFormat: 'CSV'
});

Map.addLayer(selected, {color: 'red'}, 'selected FUAs (' + BATCH + ')');
Map.centerObject(selected, 4);
