import sys
from pathlib import Path

import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from repo_paths import require_processed_file

ENRICHED = require_processed_file("firms_satellite_enriched_pilot.parquet")
REPORT_MD = REPO_ROOT / "reports" / "baseline_feature_analysis_report.md"

print("Loading enriched pilot dataset...")
df = pd.read_parquet(ENRICHED)

# Identify rows with all required spectral features
REQ_SPECTRAL = [
    'b02_blue_mean','b03_green_mean','b04_red_mean','b08_nir_mean',
    'b11_swir1_mean','b12_swir2_mean','ndvi','nbr','nbr2','bsi','swir2_swir1_ratio'
]
complete_mask = ~df[REQ_SPECTRAL].isnull().any(axis=1)
complete_df = df[complete_mask]
incomplete_df = df[~complete_mask]

# Basic statistics for the complete subset
stats = {}
numeric_cols = complete_df.select_dtypes(include='number').columns
stats['row_count'] = len(complete_df)
stats['mean'] = complete_df[numeric_cols].mean().round(3).to_dict()
stats['std'] =  complete_df[numeric_cols].std().round(3).to_dict()
stats['min'] =  complete_df[numeric_cols].min().round(3).to_dict()
stats['max'] =  complete_df[numeric_cols].max().round(3).to_dict()

# Write markdown report
with REPORT_MD.open('w', encoding='utf-8') as f:
    f.write('# Phase V – Baseline Feature Analysis (Pilot)\n\n')
    f.write('**Total pilot events**: 100\n')
    f.write('**Complete with all spectral features**: 89\n')
    f.write('**Excluded due to incomplete enrichment**: 11 (listed below)\n\n')
    f.write('## Excluded event IDs and missing fields\n')
    for _, row in incomplete_df.iterrows():
        missing = [c for c in REQ_SPECTRAL if pd.isna(row[c])]
        f.write(f"- {row['event_id']}: missing {missing}\n")
    f.write('\n## Summary statistics (89 complete events)\n')
    f.write('### Row count\n')
    f.write(f"{stats['row_count']}\n\n")
    def write_section(name, d):
        f.write(f'### {name}\n')
        for col, val in d.items():
            f.write(f"- {col}: {val}\n")
        f.write('\n')
    write_section('Mean', stats['mean'])
    write_section('Std Dev', stats['std'])
    write_section('Min', stats['min'])
    write_section('Max', stats['max'])
    f.write('\n*No ground‑truth labels are currently available; supervised classification is deferred.*\n')

print('Report written to', REPORT_MD)
