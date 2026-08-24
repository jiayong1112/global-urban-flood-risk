"""
Combine FUA data by country
Aggregate FUA-level data to country level:
- For normalized metrics: calculate mean across FUAs in each country
- For GDP metrics: calculate sum across FUAs in each country
"""

import os
from pathlib import Path

import pandas as pd

from region_map import REGION_MAP

# Define paths
import paths

# The January per-FUA exports. This was an absolute path on the original
# author machine until 2026-08 and could not run anywhere else.
FUA_DIR = paths.FUA_2026_01
OUTPUT_DIR = paths.OUTPUT

# List of continents
CONTINENTS = ["Africa", "Asia", "CSAmerica", "Europe", "NAmerica", "Oceania"]

def get_region_mapping():
    """
    Map countries to regions based on geographical location.

    The mapping itself lives in region_map.py, which is the single
    authoritative copy shared by every script in this repository. It was
    inlined here until 2026-08; that copy placed Russia in Central Asia,
    disagreeing with Table S2 and with the reported regional results.
    """
    return dict(REGION_MAP)

def combine_fua_files(file_pattern, is_gdp=False):
    """Combine FUA files from all continents"""
    all_data = []

    for continent in CONTINENTS:
        file_path = FUA_DIR / f"{continent}_{file_pattern}.csv"
        if file_path.exists():
            print(f"Reading {file_path.name}...")
            df = pd.read_csv(file_path)
            all_data.append(df)
        else:
            print(f"Warning: {file_path.name} not found")

    if not all_data:
        raise ValueError("No data files found!")

    combined = pd.concat(all_data, ignore_index=True)

    # Add region mapping
    region_map = get_region_mapping()
    combined['wld_rgn'] = combined['Cntry_name'].map(region_map)

    # Report any unmapped countries
    unmapped = combined[combined['wld_rgn'].isna()]['Cntry_name'].unique()
    if len(unmapped) > 0:
        print(f"  WARNING: {len(unmapped)} unmapped countries: {', '.join(unmapped)}")

    print(f"Combined {len(combined)} FUAs from {len(all_data)} files\n")

    return combined

def aggregate_to_country_normalized(fua_df):
    """
    Aggregate FUA data to country level using MEAN for normalized metrics
    """
    print("Aggregating normalized metrics (mean of FUAs per country)...")

    # Group by country and calculate means
    country_data = fua_df.groupby(['Cntry_name', 'wld_rgn']).agg({
        'Cntry_ISO': 'first',
        # Mean of means for normalized metrics
        'exDmg_mean': 'mean',
        'exDmg_pros_mean': 'mean',
        'exInunD_mean': 'mean',
        'exInunD_pros_mean': 'mean',
        # For depth, also take mean
        'exDep_mean': 'mean',
        # For height and protection, take mean
        'height_mean': 'mean',
        'flopros_merge_mean': 'mean',
        'flopros_model_mean': 'mean',
        # Count number of FUAs per country
        'eFUA_ID': 'count'
    }).reset_index()

    # Rename columns to match original format
    country_data.rename(columns={
        'Cntry_name': 'country_na',
        'Cntry_ISO': 'abbreviati',
        'eFUA_ID': 'n_fuas'
    }, inplace=True)

    print(f"Aggregated to {len(country_data)} countries")
    return country_data

def aggregate_to_country_gdp(fua_gdp_df):
    """
    Aggregate FUA GDP data to country level using SUM for total GDP at risk
    """
    print("Aggregating GDP metrics (sum of FUAs per country)...")

    # Group by country and calculate sums
    country_data = fua_gdp_df.groupby(['Cntry_name', 'wld_rgn']).agg({
        'Cntry_ISO': 'first',
        # Sum of GDP values across FUAs
        'exDmg_sum': 'sum',
        'exDmg_pros_sum': 'sum',
        'exInunD_sum': 'sum',
        'exInunD_pros_sum': 'sum',
        # Count number of FUAs per country
        'eFUA_ID': 'count'
    }).reset_index()

    # Rename columns to match original format
    country_data.rename(columns={
        'Cntry_name': 'country_na',
        'Cntry_ISO': 'abbreviati',
        'eFUA_ID': 'n_fuas'
    }, inplace=True)

    print(f"Aggregated to {len(country_data)} countries")
    return country_data

def main():
    print("=" * 60)
    print("Combining FUA data and aggregating to country level")
    print("=" * 60)
    print()

    # 1. Process normalized FUA data
    print("--- Processing Normalized FUA Data ---")
    fua_normalized = combine_fua_files("fua_2026-1-8", is_gdp=False)
    country_normalized = aggregate_to_country_normalized(fua_normalized)

    # Save normalized country data
    output_file = OUTPUT_DIR / "fua_world_countries_2026-1-8.csv"
    country_normalized.to_csv(output_file, index=False)
    print(f"Saved normalized country data to: {output_file}")
    print(f"Columns: {list(country_normalized.columns)}")
    print(f"\nSample data:")
    print(country_normalized.head())
    print()

    # 2. Process GDP FUA data
    print("\n--- Processing GDP FUA Data ---")
    fua_gdp = combine_fua_files("GDP_fua_2026-1-8", is_gdp=True)
    country_gdp = aggregate_to_country_gdp(fua_gdp)

    # Save GDP country data
    output_file = OUTPUT_DIR / "fua_world_countries_GDP_2026-1-8.csv"
    country_gdp.to_csv(output_file, index=False)
    print(f"Saved GDP country data to: {output_file}")
    print(f"Columns: {list(country_gdp.columns)}")
    print(f"\nSample data:")
    print(country_gdp.head())
    print()

    # 3. Summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)
    print(f"\nNormalized data:")
    print(f"  Total countries: {len(country_normalized)}")
    print(f"  Total FUAs: {country_normalized['n_fuas'].sum()}")
    print(f"  Regions: {sorted(country_normalized['wld_rgn'].unique())}")

    print(f"\nGDP data:")
    print(f"  Total countries: {len(country_gdp)}")
    print(f"  Total FUAs: {country_gdp['n_fuas'].sum()}")
    print(f"  Regions: {sorted(country_gdp['wld_rgn'].unique())}")

    # Check for negative values in GDP data
    print(f"\n--- Checking for negative GDP values ---")
    neg_exDmg = country_gdp[country_gdp['exDmg_sum'] < 0]
    neg_exDmg_pros = country_gdp[country_gdp['exDmg_pros_sum'] < 0]

    if len(neg_exDmg) > 0:
        print(f"WARNING: Found {len(neg_exDmg)} countries with negative exDmg_sum:")
        print(neg_exDmg[['country_na', 'wld_rgn', 'exDmg_sum', 'n_fuas']])
    else:
        print("✓ No negative exDmg_sum values found")

    if len(neg_exDmg_pros) > 0:
        print(f"WARNING: Found {len(neg_exDmg_pros)} countries with negative exDmg_pros_sum:")
        print(neg_exDmg_pros[['country_na', 'wld_rgn', 'exDmg_pros_sum', 'n_fuas']])
    else:
        print("✓ No negative exDmg_pros_sum values found")

    print("\n" + "=" * 60)
    print("Done! FUA data combined and aggregated to country level")
    print("=" * 60)

if __name__ == "__main__":
    main()
