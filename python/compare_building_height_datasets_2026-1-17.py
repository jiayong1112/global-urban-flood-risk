"""
Compare flood risk estimates across JRC, WSF3D, and GBH2020 building height datasets
Updated for csv_fua_2026-1-17 data

Date: 2026-01-17
Author: Analysis script for "Above and Beyond" paper
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Data directory
data_dir = '/Users/jiayongliang/Documents/Trae/inAbove_Flood_SR/Scientific Reports/2026-1 submission/csv_fua_2026-1-17/'
output_dir = '/Users/jiayongliang/Documents/Trae/inAbove_Flood_SR/Scientific Reports/2026-1 submission/figures/'

# Regions to process
regions = ['Africa', 'Asia', 'CSAmerica', 'Europe', 'NAmerica', 'Oceania']

print("="*80)
print("BUILDING HEIGHT DATASET COMPARISON - 2026-01-17 Data")
print("="*80)
print()

# Load and combine all data
all_data = []

for region in regions:
    print(f"Loading {region} data...")

    # JRC
    jrc_file = os.path.join(data_dir, f'JRC_{region}_FloodRisk.csv')
    jrc = pd.read_csv(jrc_file)
    jrc['dataset'] = 'JRC'
    jrc['region'] = region

    # WSF3D - Use CORRECTED version if available
    wsf3d_file_corrected = os.path.join(data_dir, f'WSF3D_{region}_FloodRisk_CORRECTED.csv')
    wsf3d_file = os.path.join(data_dir, f'WSF3D_{region}_FloodRisk.csv')

    if os.path.exists(wsf3d_file_corrected):
        print(f"  Using CORRECTED WSF3D file for {region}")
        wsf3d = pd.read_csv(wsf3d_file_corrected)
    else:
        wsf3d = pd.read_csv(wsf3d_file)
    wsf3d['dataset'] = 'WSF3D'
    wsf3d['region'] = region

    # GBH2020
    gbh_file = os.path.join(data_dir, f'GBH2020_{region}_FloodRisk.csv')
    gbh = pd.read_csv(gbh_file)
    gbh['dataset'] = 'GBH2020'
    gbh['region'] = region

    # Combine
    all_data.extend([jrc, wsf3d, gbh])
    print(f"  JRC: {len(jrc)} FUAs, WSF3D: {len(wsf3d)} FUAs, GBH2020: {len(gbh)} FUAs")

# Concatenate all data
df_all = pd.concat(all_data, ignore_index=True)

print(f"\nTotal records: {len(df_all)}")
print(f"Records per dataset:")
print(df_all.groupby('dataset').size())
print()

# Pivot data for comparison (merge on eFUA_name)
print("Merging datasets for direct comparison...")

# First merge JRC and WSF3D
jrc_data = df_all[df_all['dataset'] == 'JRC'][['eFUA_name', 'Cntry_name', 'height_mean', 'exDmg_mean', 'exInunD_mean', 'exDep_mean']].copy()
wsf3d_data = df_all[df_all['dataset'] == 'WSF3D'][['eFUA_name', 'height_mean', 'exDmg_mean', 'exInunD_mean']].copy()
gbh_data = df_all[df_all['dataset'] == 'GBH2020'][['eFUA_name', 'height_mean', 'exDmg_mean', 'exInunD_mean']].copy()

# Merge all three
comparison = jrc_data.merge(
    wsf3d_data,
    on='eFUA_name',
    suffixes=('_jrc', '_wsf3d'),
    how='inner'
).merge(
    gbh_data,
    on='eFUA_name',
    how='inner'
)

# Rename GBH columns
comparison.rename(columns={
    'height_mean': 'height_mean_gbh',
    'exDmg_mean': 'exDmg_mean_gbh',
    'exInunD_mean': 'exInunD_mean_gbh'
}, inplace=True)

print(f"FUAs with data in all three datasets: {len(comparison)}")
print()

# Remove any rows with missing values
comparison_clean = comparison.dropna()
print(f"FUAs after removing missing values: {len(comparison_clean)}")
print()

# Save comparison dataset
comparison_clean.to_csv(os.path.join(data_dir, '../dataset_comparison_2026-1-17.csv'), index=False)
print(f"Saved comparison dataset to: dataset_comparison_2026-1-17.csv")
print()

# ============================================================================
# ANALYSIS 1: BUILDING HEIGHT COMPARISON
# ============================================================================
print("="*80)
print("1. BUILDING HEIGHT COMPARISON")
print("="*80)
print()

height_stats = pd.DataFrame({
    'JRC': comparison_clean['height_mean_jrc'].describe(),
    'WSF3D': comparison_clean['height_mean_wsf3d'].describe(),
    'GBH2020': comparison_clean['height_mean_gbh'].describe()
})

print("Building Height Statistics (meters):")
print(height_stats.round(2))
print()

# Correlations
print("Building Height Correlations:")
print(f"  JRC vs WSF3D:   r = {comparison_clean[['height_mean_jrc', 'height_mean_wsf3d']].corr().iloc[0,1]:.3f}")
print(f"  JRC vs GBH2020: r = {comparison_clean[['height_mean_jrc', 'height_mean_gbh']].corr().iloc[0,1]:.3f}")
print(f"  WSF3D vs GBH:   r = {comparison_clean[['height_mean_wsf3d', 'height_mean_gbh']].corr().iloc[0,1]:.3f}")
print()

# Mean differences
print("Mean Height Differences:")
print(f"  WSF3D - JRC:   {(comparison_clean['height_mean_wsf3d'] - comparison_clean['height_mean_jrc']).mean():.2f} m ({(comparison_clean['height_mean_wsf3d'] / comparison_clean['height_mean_jrc']).mean()*100 - 100:.1f}%)")
print(f"  GBH - JRC:     {(comparison_clean['height_mean_gbh'] - comparison_clean['height_mean_jrc']).mean():.2f} m ({(comparison_clean['height_mean_gbh'] / comparison_clean['height_mean_jrc']).mean()*100 - 100:.1f}%)")
print(f"  GBH - WSF3D:   {(comparison_clean['height_mean_gbh'] - comparison_clean['height_mean_wsf3d']).mean():.2f} m ({(comparison_clean['height_mean_gbh'] / comparison_clean['height_mean_wsf3d']).mean()*100 - 100:.1f}%)")
print()

# ============================================================================
# ANALYSIS 2: FLOOD-DEPTH DAMAGE (FD-AED) COMPARISON
# ============================================================================
print("="*80)
print("2. FLOOD-DEPTH DAMAGE (FD-AED) COMPARISON")
print("="*80)
print()

fd_stats = pd.DataFrame({
    'JRC': comparison_clean['exDmg_mean_jrc'].describe(),
    'WSF3D': comparison_clean['exDmg_mean_wsf3d'].describe(),
    'GBH2020': comparison_clean['exDmg_mean_gbh'].describe()
})

print("FD-AED Statistics (%):")
print((fd_stats * 100).round(2))
print()

# Correlations
print("FD-AED Correlations:")
print(f"  JRC vs WSF3D:   r = {comparison_clean[['exDmg_mean_jrc', 'exDmg_mean_wsf3d']].corr().iloc[0,1]:.3f}")
print(f"  JRC vs GBH2020: r = {comparison_clean[['exDmg_mean_jrc', 'exDmg_mean_gbh']].corr().iloc[0,1]:.3f}")
print(f"  WSF3D vs GBH:   r = {comparison_clean[['exDmg_mean_wsf3d', 'exDmg_mean_gbh']].corr().iloc[0,1]:.3f}")
print()

# Mean differences
print("Mean FD-AED Differences (percentage points):")
print(f"  WSF3D - JRC:   {(comparison_clean['exDmg_mean_wsf3d'] - comparison_clean['exDmg_mean_jrc']).mean()*100:.4f}% ({(comparison_clean['exDmg_mean_wsf3d'] / comparison_clean['exDmg_mean_jrc']).mean()*100 - 100:.1f}% relative)")
print(f"  GBH - JRC:     {(comparison_clean['exDmg_mean_gbh'] - comparison_clean['exDmg_mean_jrc']).mean()*100:.4f}% ({(comparison_clean['exDmg_mean_gbh'] / comparison_clean['exDmg_mean_jrc']).mean()*100 - 100:.1f}% relative)")
print(f"  GBH - WSF3D:   {(comparison_clean['exDmg_mean_gbh'] - comparison_clean['exDmg_mean_wsf3d']).mean()*100:.4f}% ({(comparison_clean['exDmg_mean_gbh'] / comparison_clean['exDmg_mean_wsf3d']).mean()*100 - 100:.1f}% relative)")
print()

# ============================================================================
# ANALYSIS 3: INUNDATION-RATIO DAMAGE (IR-AED) COMPARISON
# ============================================================================
print("="*80)
print("3. INUNDATION-RATIO DAMAGE (IR-AED) COMPARISON")
print("="*80)
print()

ir_stats = pd.DataFrame({
    'JRC': comparison_clean['exInunD_mean_jrc'].describe(),
    'WSF3D': comparison_clean['exInunD_mean_wsf3d'].describe(),
    'GBH2020': comparison_clean['exInunD_mean_gbh'].describe()
})

print("IR-AED Statistics (%):")
print((ir_stats * 100).round(2))
print()

# Correlations
print("IR-AED Correlations:")
print(f"  JRC vs WSF3D:   r = {comparison_clean[['exInunD_mean_jrc', 'exInunD_mean_wsf3d']].corr().iloc[0,1]:.3f}")
print(f"  JRC vs GBH2020: r = {comparison_clean[['exInunD_mean_jrc', 'exInunD_mean_gbh']].corr().iloc[0,1]:.3f}")
print(f"  WSF3D vs GBH:   r = {comparison_clean[['exInunD_mean_wsf3d', 'exInunD_mean_gbh']].corr().iloc[0,1]:.3f}")
print()

# Mean differences
print("Mean IR-AED Differences (percentage points):")
print(f"  WSF3D - JRC:   {(comparison_clean['exInunD_mean_wsf3d'] - comparison_clean['exInunD_mean_jrc']).mean()*100:.4f}% ({(comparison_clean['exInunD_mean_wsf3d'] / comparison_clean['exInunD_mean_jrc']).mean()*100 - 100:.1f}% relative)")
print(f"  GBH - JRC:     {(comparison_clean['exInunD_mean_gbh'] - comparison_clean['exInunD_mean_jrc']).mean()*100:.4f}% ({(comparison_clean['exInunD_mean_gbh'] / comparison_clean['exInunD_mean_jrc']).mean()*100 - 100:.1f}% relative)")
print(f"  GBH - WSF3D:   {(comparison_clean['exInunD_mean_gbh'] - comparison_clean['exInunD_mean_wsf3d']).mean()*100:.4f}% ({(comparison_clean['exInunD_mean_gbh'] / comparison_clean['exInunD_mean_wsf3d']).mean()*100 - 100:.1f}% relative)")
print()

# ============================================================================
# VISUALIZATIONS
# ============================================================================
print("="*80)
print("GENERATING VISUALIZATIONS")
print("="*80)
print()

# Figure 1: Scatter plots comparing datasets
fig, axes = plt.subplots(3, 3, figsize=(18, 18))

# Row 1: Building Heights
# JRC vs WSF3D
axes[0, 0].scatter(comparison_clean['height_mean_jrc'], comparison_clean['height_mean_wsf3d'],
                   alpha=0.5, s=20, edgecolors='none')
axes[0, 0].plot([0, comparison_clean['height_mean_jrc'].max()],
                [0, comparison_clean['height_mean_jrc'].max()], 'r--', linewidth=2, label='1:1 line')
axes[0, 0].set_xlabel('JRC Building Height (m)', fontsize=11)
axes[0, 0].set_ylabel('WSF3D Building Height (m)', fontsize=11)
axes[0, 0].set_title(f'JRC vs WSF3D Heights\nr = {comparison_clean[["height_mean_jrc", "height_mean_wsf3d"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# JRC vs GBH
axes[0, 1].scatter(comparison_clean['height_mean_jrc'], comparison_clean['height_mean_gbh'],
                   alpha=0.5, s=20, edgecolors='none')
axes[0, 1].plot([0, comparison_clean['height_mean_jrc'].max()],
                [0, comparison_clean['height_mean_jrc'].max()], 'r--', linewidth=2, label='1:1 line')
axes[0, 1].set_xlabel('JRC Building Height (m)', fontsize=11)
axes[0, 1].set_ylabel('GBH2020 Building Height (m)', fontsize=11)
axes[0, 1].set_title(f'JRC vs GBH2020 Heights\nr = {comparison_clean[["height_mean_jrc", "height_mean_gbh"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# WSF3D vs GBH
axes[0, 2].scatter(comparison_clean['height_mean_wsf3d'], comparison_clean['height_mean_gbh'],
                   alpha=0.5, s=20, edgecolors='none')
axes[0, 2].plot([0, comparison_clean['height_mean_wsf3d'].max()],
                [0, comparison_clean['height_mean_wsf3d'].max()], 'r--', linewidth=2, label='1:1 line')
axes[0, 2].set_xlabel('WSF3D Building Height (m)', fontsize=11)
axes[0, 2].set_ylabel('GBH2020 Building Height (m)', fontsize=11)
axes[0, 2].set_title(f'WSF3D vs GBH2020 Heights\nr = {comparison_clean[["height_mean_wsf3d", "height_mean_gbh"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[0, 2].legend()
axes[0, 2].grid(True, alpha=0.3)

# Row 2: FD-AED
# JRC vs WSF3D
axes[1, 0].scatter(comparison_clean['exDmg_mean_jrc']*100, comparison_clean['exDmg_mean_wsf3d']*100,
                   alpha=0.5, s=20, edgecolors='none')
axes[1, 0].plot([0, comparison_clean['exDmg_mean_jrc'].max()*100],
                [0, comparison_clean['exDmg_mean_jrc'].max()*100], 'r--', linewidth=2, label='1:1 line')
axes[1, 0].set_xlabel('JRC FD-AED (%)', fontsize=11)
axes[1, 0].set_ylabel('WSF3D FD-AED (%)', fontsize=11)
axes[1, 0].set_title(f'JRC vs WSF3D FD-AED\nr = {comparison_clean[["exDmg_mean_jrc", "exDmg_mean_wsf3d"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# JRC vs GBH
axes[1, 1].scatter(comparison_clean['exDmg_mean_jrc']*100, comparison_clean['exDmg_mean_gbh']*100,
                   alpha=0.5, s=20, edgecolors='none')
axes[1, 1].plot([0, comparison_clean['exDmg_mean_jrc'].max()*100],
                [0, comparison_clean['exDmg_mean_jrc'].max()*100], 'r--', linewidth=2, label='1:1 line')
axes[1, 1].set_xlabel('JRC FD-AED (%)', fontsize=11)
axes[1, 1].set_ylabel('GBH2020 FD-AED (%)', fontsize=11)
axes[1, 1].set_title(f'JRC vs GBH2020 FD-AED\nr = {comparison_clean[["exDmg_mean_jrc", "exDmg_mean_gbh"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

# WSF3D vs GBH
axes[1, 2].scatter(comparison_clean['exDmg_mean_wsf3d']*100, comparison_clean['exDmg_mean_gbh']*100,
                   alpha=0.5, s=20, edgecolors='none')
axes[1, 2].plot([0, comparison_clean['exDmg_mean_wsf3d'].max()*100],
                [0, comparison_clean['exDmg_mean_wsf3d'].max()*100], 'r--', linewidth=2, label='1:1 line')
axes[1, 2].set_xlabel('WSF3D FD-AED (%)', fontsize=11)
axes[1, 2].set_ylabel('GBH2020 FD-AED (%)', fontsize=11)
axes[1, 2].set_title(f'WSF3D vs GBH2020 FD-AED\nr = {comparison_clean[["exDmg_mean_wsf3d", "exDmg_mean_gbh"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[1, 2].legend()
axes[1, 2].grid(True, alpha=0.3)

# Row 3: IR-AED
# JRC vs WSF3D
axes[2, 0].scatter(comparison_clean['exInunD_mean_jrc']*100, comparison_clean['exInunD_mean_wsf3d']*100,
                   alpha=0.5, s=20, edgecolors='none')
axes[2, 0].plot([0, comparison_clean['exInunD_mean_jrc'].max()*100],
                [0, comparison_clean['exInunD_mean_jrc'].max()*100], 'r--', linewidth=2, label='1:1 line')
axes[2, 0].set_xlabel('JRC IR-AED (%)', fontsize=11)
axes[2, 0].set_ylabel('WSF3D IR-AED (%)', fontsize=11)
axes[2, 0].set_title(f'JRC vs WSF3D IR-AED\nr = {comparison_clean[["exInunD_mean_jrc", "exInunD_mean_wsf3d"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[2, 0].legend()
axes[2, 0].grid(True, alpha=0.3)

# JRC vs GBH
axes[2, 1].scatter(comparison_clean['exInunD_mean_jrc']*100, comparison_clean['exInunD_mean_gbh']*100,
                   alpha=0.5, s=20, edgecolors='none')
axes[2, 1].plot([0, comparison_clean['exInunD_mean_jrc'].max()*100],
                [0, comparison_clean['exInunD_mean_jrc'].max()*100], 'r--', linewidth=2, label='1:1 line')
axes[2, 1].set_xlabel('JRC IR-AED (%)', fontsize=11)
axes[2, 1].set_ylabel('GBH2020 IR-AED (%)', fontsize=11)
axes[2, 1].set_title(f'JRC vs GBH2020 IR-AED\nr = {comparison_clean[["exInunD_mean_jrc", "exInunD_mean_gbh"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[2, 1].legend()
axes[2, 1].grid(True, alpha=0.3)

# WSF3D vs GBH
axes[2, 2].scatter(comparison_clean['exInunD_mean_wsf3d']*100, comparison_clean['exInunD_mean_gbh']*100,
                   alpha=0.5, s=20, edgecolors='none')
axes[2, 2].plot([0, comparison_clean['exInunD_mean_wsf3d'].max()*100],
                [0, comparison_clean['exInunD_mean_wsf3d'].max()*100], 'r--', linewidth=2, label='1:1 line')
axes[2, 2].set_xlabel('WSF3D IR-AED (%)', fontsize=11)
axes[2, 2].set_ylabel('GBH2020 IR-AED (%)', fontsize=11)
axes[2, 2].set_title(f'WSF3D vs GBH2020 IR-AED\nr = {comparison_clean[["exInunD_mean_wsf3d", "exInunD_mean_gbh"]].corr().iloc[0,1]:.3f}', fontsize=12)
axes[2, 2].legend()
axes[2, 2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'dataset_comparison_scatter_2026-1-17.png'), dpi=300, bbox_inches='tight')
print(f"Saved: {output_dir}dataset_comparison_scatter_2026-1-17.png")
plt.close()

# Figure 2: Box plots
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Building heights
height_data = pd.DataFrame({
    'JRC': comparison_clean['height_mean_jrc'],
    'WSF3D': comparison_clean['height_mean_wsf3d'],
    'GBH2020': comparison_clean['height_mean_gbh']
})
height_data.boxplot(ax=axes[0])
axes[0].set_ylabel('Building Height (m)', fontsize=12)
axes[0].set_title('Building Height Distribution', fontsize=13, fontweight='bold')
axes[0].grid(True, alpha=0.3)

# FD-AED
fd_data = pd.DataFrame({
    'JRC': comparison_clean['exDmg_mean_jrc'] * 100,
    'WSF3D': comparison_clean['exDmg_mean_wsf3d'] * 100,
    'GBH2020': comparison_clean['exDmg_mean_gbh'] * 100
})
fd_data.boxplot(ax=axes[1])
axes[1].set_ylabel('FD-AED (%)', fontsize=12)
axes[1].set_title('Flood-Depth Damage (FD-AED)', fontsize=13, fontweight='bold')
axes[1].grid(True, alpha=0.3)

# IR-AED
ir_data = pd.DataFrame({
    'JRC': comparison_clean['exInunD_mean_jrc'] * 100,
    'WSF3D': comparison_clean['exInunD_mean_wsf3d'] * 100,
    'GBH2020': comparison_clean['exInunD_mean_gbh'] * 100
})
ir_data.boxplot(ax=axes[2])
axes[2].set_ylabel('IR-AED (%)', fontsize=12)
axes[2].set_title('Inundation-Ratio Damage (IR-AED)', fontsize=13, fontweight='bold')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'dataset_comparison_boxplot_2026-1-17.png'), dpi=300, bbox_inches='tight')
print(f"Saved: {output_dir}dataset_comparison_boxplot_2026-1-17.png")
plt.close()

# Figure 3: Bland-Altman style difference plots
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Row 1: Building height differences
# WSF3D - JRC
mean_h1 = (comparison_clean['height_mean_wsf3d'] + comparison_clean['height_mean_jrc']) / 2
diff_h1 = comparison_clean['height_mean_wsf3d'] - comparison_clean['height_mean_jrc']
axes[0, 0].scatter(mean_h1, diff_h1, alpha=0.5, s=20, edgecolors='none')
axes[0, 0].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[0, 0].axhline(y=diff_h1.mean(), color='b', linestyle='-', linewidth=2, label=f'Mean diff: {diff_h1.mean():.1f}m')
axes[0, 0].set_xlabel('Mean Height (m)', fontsize=11)
axes[0, 0].set_ylabel('WSF3D - JRC (m)', fontsize=11)
axes[0, 0].set_title('Height Difference: WSF3D - JRC', fontsize=12)
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# GBH - JRC
mean_h2 = (comparison_clean['height_mean_gbh'] + comparison_clean['height_mean_jrc']) / 2
diff_h2 = comparison_clean['height_mean_gbh'] - comparison_clean['height_mean_jrc']
axes[0, 1].scatter(mean_h2, diff_h2, alpha=0.5, s=20, edgecolors='none')
axes[0, 1].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[0, 1].axhline(y=diff_h2.mean(), color='b', linestyle='-', linewidth=2, label=f'Mean diff: {diff_h2.mean():.1f}m')
axes[0, 1].set_xlabel('Mean Height (m)', fontsize=11)
axes[0, 1].set_ylabel('GBH2020 - JRC (m)', fontsize=11)
axes[0, 1].set_title('Height Difference: GBH2020 - JRC', fontsize=12)
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# GBH - WSF3D
mean_h3 = (comparison_clean['height_mean_gbh'] + comparison_clean['height_mean_wsf3d']) / 2
diff_h3 = comparison_clean['height_mean_gbh'] - comparison_clean['height_mean_wsf3d']
axes[0, 2].scatter(mean_h3, diff_h3, alpha=0.5, s=20, edgecolors='none')
axes[0, 2].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[0, 2].axhline(y=diff_h3.mean(), color='b', linestyle='-', linewidth=2, label=f'Mean diff: {diff_h3.mean():.1f}m')
axes[0, 2].set_xlabel('Mean Height (m)', fontsize=11)
axes[0, 2].set_ylabel('GBH2020 - WSF3D (m)', fontsize=11)
axes[0, 2].set_title('Height Difference: GBH2020 - WSF3D', fontsize=12)
axes[0, 2].legend()
axes[0, 2].grid(True, alpha=0.3)

# Row 2: FD-AED differences
# WSF3D - JRC
mean_fd1 = (comparison_clean['exDmg_mean_wsf3d'] + comparison_clean['exDmg_mean_jrc']) / 2 * 100
diff_fd1 = (comparison_clean['exDmg_mean_wsf3d'] - comparison_clean['exDmg_mean_jrc']) * 100
axes[1, 0].scatter(mean_fd1, diff_fd1, alpha=0.5, s=20, edgecolors='none')
axes[1, 0].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[1, 0].axhline(y=diff_fd1.mean(), color='b', linestyle='-', linewidth=2, label=f'Mean diff: {diff_fd1.mean():.3f}%')
axes[1, 0].set_xlabel('Mean FD-AED (%)', fontsize=11)
axes[1, 0].set_ylabel('WSF3D - JRC (%-points)', fontsize=11)
axes[1, 0].set_title('FD-AED Difference: WSF3D - JRC', fontsize=12)
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# GBH - JRC
mean_fd2 = (comparison_clean['exDmg_mean_gbh'] + comparison_clean['exDmg_mean_jrc']) / 2 * 100
diff_fd2 = (comparison_clean['exDmg_mean_gbh'] - comparison_clean['exDmg_mean_jrc']) * 100
axes[1, 1].scatter(mean_fd2, diff_fd2, alpha=0.5, s=20, edgecolors='none')
axes[1, 1].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[1, 1].axhline(y=diff_fd2.mean(), color='b', linestyle='-', linewidth=2, label=f'Mean diff: {diff_fd2.mean():.3f}%')
axes[1, 1].set_xlabel('Mean FD-AED (%)', fontsize=11)
axes[1, 1].set_ylabel('GBH2020 - JRC (%-points)', fontsize=11)
axes[1, 1].set_title('FD-AED Difference: GBH2020 - JRC', fontsize=12)
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

# GBH - WSF3D
mean_fd3 = (comparison_clean['exDmg_mean_gbh'] + comparison_clean['exDmg_mean_wsf3d']) / 2 * 100
diff_fd3 = (comparison_clean['exDmg_mean_gbh'] - comparison_clean['exDmg_mean_wsf3d']) * 100
axes[1, 2].scatter(mean_fd3, diff_fd3, alpha=0.5, s=20, edgecolors='none')
axes[1, 2].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[1, 2].axhline(y=diff_fd3.mean(), color='b', linestyle='-', linewidth=2, label=f'Mean diff: {diff_fd3.mean():.3f}%')
axes[1, 2].set_xlabel('Mean FD-AED (%)', fontsize=11)
axes[1, 2].set_ylabel('GBH2020 - WSF3D (%-points)', fontsize=11)
axes[1, 2].set_title('FD-AED Difference: GBH2020 - WSF3D', fontsize=12)
axes[1, 2].legend()
axes[1, 2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'dataset_comparison_differences_2026-1-17.png'), dpi=300, bbox_inches='tight')
print(f"Saved: {output_dir}dataset_comparison_differences_2026-1-17.png")
plt.close()

# ============================================================================
# SUMMARY STATISTICS TABLE
# ============================================================================
print()
print("="*80)
print("SUMMARY TABLE FOR PAPER")
print("="*80)
print()

summary_table = pd.DataFrame({
    'Metric': ['Building Height (m)', 'FD-AED (%)', 'IR-AED (%)'],
    'JRC Mean': [
        comparison_clean['height_mean_jrc'].mean(),
        comparison_clean['exDmg_mean_jrc'].mean() * 100,
        comparison_clean['exInunD_mean_jrc'].mean() * 100
    ],
    'JRC SD': [
        comparison_clean['height_mean_jrc'].std(),
        comparison_clean['exDmg_mean_jrc'].std() * 100,
        comparison_clean['exInunD_mean_jrc'].std() * 100
    ],
    'WSF3D Mean': [
        comparison_clean['height_mean_wsf3d'].mean(),
        comparison_clean['exDmg_mean_wsf3d'].mean() * 100,
        comparison_clean['exInunD_mean_wsf3d'].mean() * 100
    ],
    'WSF3D SD': [
        comparison_clean['height_mean_wsf3d'].std(),
        comparison_clean['exDmg_mean_wsf3d'].std() * 100,
        comparison_clean['exInunD_mean_wsf3d'].std() * 100
    ],
    'GBH2020 Mean': [
        comparison_clean['height_mean_gbh'].mean(),
        comparison_clean['exDmg_mean_gbh'].mean() * 100,
        comparison_clean['exInunD_mean_gbh'].mean() * 100
    ],
    'GBH2020 SD': [
        comparison_clean['height_mean_gbh'].std(),
        comparison_clean['exDmg_mean_gbh'].std() * 100,
        comparison_clean['exInunD_mean_gbh'].std() * 100
    ],
    'CV (%)': [
        np.std([comparison_clean['height_mean_jrc'].mean(),
                comparison_clean['height_mean_wsf3d'].mean(),
                comparison_clean['height_mean_gbh'].mean()]) /
        np.mean([comparison_clean['height_mean_jrc'].mean(),
                 comparison_clean['height_mean_wsf3d'].mean(),
                 comparison_clean['height_mean_gbh'].mean()]) * 100,
        np.std([comparison_clean['exDmg_mean_jrc'].mean(),
                comparison_clean['exDmg_mean_wsf3d'].mean(),
                comparison_clean['exDmg_mean_gbh'].mean()]) /
        np.mean([comparison_clean['exDmg_mean_jrc'].mean(),
                 comparison_clean['exDmg_mean_wsf3d'].mean(),
                 comparison_clean['exDmg_mean_gbh'].mean()]) * 100,
        np.std([comparison_clean['exInunD_mean_jrc'].mean(),
                comparison_clean['exInunD_mean_wsf3d'].mean(),
                comparison_clean['exInunD_mean_gbh'].mean()]) /
        np.mean([comparison_clean['exInunD_mean_jrc'].mean(),
                 comparison_clean['exInunD_mean_wsf3d'].mean(),
                 comparison_clean['exInunD_mean_gbh'].mean()]) * 100
    ]
})

print(summary_table.round(2))
print()

summary_table.to_csv(os.path.join(output_dir, 'dataset_comparison_summary_2026-1-17.csv'), index=False)
print(f"Saved summary table to: {output_dir}dataset_comparison_summary_2026-1-17.csv")
print()

print("="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print()
print(f"Total FUAs analyzed: {len(comparison_clean)}")
print(f"Outputs saved to: {output_dir}")
print()
