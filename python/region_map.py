# -*- coding: utf-8 -*-
"""The country-to-region mapping used by every analysis in this repository.

This is the single authoritative copy. It corresponds to Table S2 of the paper
and is derived from the USDOS LSIB `wld_rgn` attribute with one deliberate
departure:

  * **Russia is assigned to Europe.** The raw LSIB attribute places it in
    Central Asia. Earlier versions of `combine_fua_data.py`,
    `compute_gdp_normalized_2026-7.py` and `a3_integration_diagnostics.py`
    each carried their own copy of this mapping, and the copies disagreed on
    exactly this country, which changed every regional row of Supplementary
    Tables S5 and S7. Russia contributes 10 functional urban areas to the
    integration-diagnostics sample and 15 to the main assembled series.

Caribbean countries are mapped to Central America. Only the Dominican Republic
carries a functional urban area in the main assembled series; Cuba, Haiti,
Jamaica and Puerto Rico appear in the integration-diagnostics sample only.

Country names are the space-free spellings used by the Earth Engine exports.
Import this module rather than re-declaring the mapping:

    from region_map import REGION_MAP, DISPLAY
"""

REGION_MAP = {
    # Africa (39)
    'Algeria': 'Africa', 'Angola': 'Africa', 'Benin': 'Africa',
    'BurkinaFaso': 'Africa', 'Cameroon': 'Africa', 'CentralAfricanRepublic': 'Africa',
    'Chad': 'Africa', 'Congo(DRC)': 'Africa', 'CotedIvoire': 'Africa',
    'DemocraticRepublicoftheCongo': 'Africa', 'Egypt': 'Africa', 'Ethiopia': 'Africa',
    'Ghana': 'Africa', 'Guinea': 'Africa', 'Kenya': 'Africa', 'Liberia': 'Africa',
    'Libya': 'Africa', 'Madagascar': 'Africa', 'Malawi': 'Africa', 'Mali': 'Africa',
    'Mauritania': 'Africa', 'Morocco': 'Africa', 'Mozambique': 'Africa',
    'Namibia': 'Africa', 'Niger': 'Africa', 'Nigeria': 'Africa',
    'RepublicofCongo': 'Africa', 'Rwanda': 'Africa', 'Senegal': 'Africa',
    'SierraLeone': 'Africa', 'Somalia': 'Africa', 'SouthAfrica': 'Africa',
    'Sudan': 'Africa', 'Tanzania': 'Africa', 'Togo': 'Africa', 'Tunisia': 'Africa',
    'Uganda': 'Africa', 'Zambia': 'Africa', 'Zimbabwe': 'Africa',

    # Central America (11)
    'CostaRica': 'C America', 'Cuba': 'C America', 'DominicanRepublic': 'C America',
    'ElSalvador': 'C America', 'Guatemala': 'C America', 'Haiti': 'C America',
    'Honduras': 'C America', 'Jamaica': 'C America', 'Nicaragua': 'C America',
    'Panama': 'C America', 'PuertoRico': 'C America',

    # South America (10)
    'Argentina': 'S America', 'Bolivia': 'S America', 'Brazil': 'S America',
    'Chile': 'S America', 'Colombia': 'S America', 'Ecuador': 'S America',
    'Paraguay': 'S America', 'Peru': 'S America', 'Uruguay': 'S America',
    'Venezuela': 'S America',

    # North America (3)
    'Canada': 'N America', 'Mexico': 'N America', 'UnitedStates': 'N America',

    # Europe (32)
    'Albania': 'Europe', 'Austria': 'Europe', 'Belarus': 'Europe', 'Belgium': 'Europe',
    'Bosnia': 'Europe', 'Bulgaria': 'Europe', 'Croatia': 'Europe',
    'CzechRepublic': 'Europe', 'Czechia': 'Europe', 'Denmark': 'Europe',
    'Finland': 'Europe', 'France': 'Europe', 'Germany': 'Europe', 'Greece': 'Europe',
    'Hungary': 'Europe', 'Ireland': 'Europe', 'Italy': 'Europe', 'Moldova': 'Europe',
    'Netherlands': 'Europe', 'Norway': 'Europe', 'Poland': 'Europe',
    'Portugal': 'Europe', 'Romania': 'Europe', 'Russia': 'Europe', 'Serbia': 'Europe',
    'Slovakia': 'Europe', 'Spain': 'Europe', 'Sweden': 'Europe',
    'Switzerland': 'Europe', 'Ukraine': 'Europe', 'UnitedKingdom': 'Europe',
    'UnitedKingdom(Scotland)': 'Europe',

    # East Asia (7)
    'China': 'E Asia', 'HongKong': 'E Asia', 'Japan': 'E Asia', 'Mongolia': 'E Asia',
    'NorthKorea': 'E Asia', 'SouthKorea': 'E Asia', 'Taiwan': 'E Asia',

    # Southeast Asia (11)
    'Brunei': 'SE Asia', 'Burma': 'SE Asia', 'Cambodia': 'SE Asia',
    'Indonesia': 'SE Asia', 'Laos': 'SE Asia', 'Malaysia': 'SE Asia',
    'Myanmar': 'SE Asia', 'Philippines': 'SE Asia', 'Singapore': 'SE Asia',
    'Thailand': 'SE Asia', 'Vietnam': 'SE Asia',

    # South Asia (6)
    'Afghanistan': 'S Asia', 'Bangladesh': 'S Asia', 'India': 'S Asia',
    'Nepal': 'S Asia', 'Pakistan': 'S Asia', 'SriLanka': 'S Asia',

    # Southwest Asia (18)
    'Armenia': 'SW Asia', 'Azerbaijan': 'SW Asia', 'Bahrain': 'SW Asia',
    'Georgia': 'SW Asia', 'Iran': 'SW Asia', 'Iraq': 'SW Asia', 'Israel': 'SW Asia',
    'Jordan': 'SW Asia', 'Kuwait': 'SW Asia', 'Lebanon': 'SW Asia', 'Oman': 'SW Asia',
    'Palestina': 'SW Asia', 'Qatar': 'SW Asia', 'SaudiArabia': 'SW Asia',
    'Syria': 'SW Asia', 'Turkey': 'SW Asia', 'UnitedArabEmirates': 'SW Asia',
    'Yemen': 'SW Asia',

    # Central Asia (5)
    'Kazakhstan': 'C Asia', 'Kyrgyzstan': 'C Asia', 'Tajikistan': 'C Asia',
    'Turkmenistan': 'C Asia', 'Uzbekistan': 'C Asia',

    # Oceania (4)
    'Australia': 'Oceania', 'Fiji': 'Oceania', 'NewZealand': 'Oceania',
    'PapuaNewGuinea': 'Oceania',

}

# Long-form region names used in figure legends and table headers.
DISPLAY = {
    "Africa": "Africa",
    "C America": "Central America",
    "S America": "South America",
    "N America": "North America",
    "Europe": "Europe",
    "E Asia": "East Asia",
    "SE Asia": "Southeast Asia",
    "S Asia": "South Asia",
    "SW Asia": "Southwest Asia",
    "C Asia": "Central Asia",
    "Oceania": "Oceania",
}

# The superseded mapping, kept so that figures which illustrate the correction
# can show both. It differs from REGION_MAP in Russia alone.
PUBLISHED_REGION_MAP = dict(REGION_MAP, Russia="C Asia")

# Countries whose assignment changed in the 2026-08 revision.
CORRECTIONS = {k: (PUBLISHED_REGION_MAP[k], REGION_MAP[k])
               for k in REGION_MAP if PUBLISHED_REGION_MAP[k] != REGION_MAP[k]}


if __name__ == "__main__":
    print(f"{len(REGION_MAP)} countries, {len(set(REGION_MAP.values()))} regions")
    for k, (old, new) in sorted(CORRECTIONS.items()):
        print(f"  {k}: {old} -> {new}")
