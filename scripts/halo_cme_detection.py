# Updated Detection Script (halo_cme_detection.py) with Enhanced Sensitivity, Merging, Filtering, and Categorization

import pandas as pd
import numpy as np
from datetime import timedelta
import os

# Load dataset
swis_data = pd.read_csv('../data/final_dataset.csv', parse_dates=['Time'])
catalog = pd.read_csv('../data/cactus/halo_cmes.csv', parse_dates=['Launch_Time', 'Expected_Start', 'Expected_End'])

# Set parameters
MIN_DURATION = timedelta(minutes=30)
ROLLING_WINDOW = 15  # smaller to capture finer variation
PERCENTILE_THRESHOLD = 90
COMPOSITE_THRESHOLD_MIN = 2.0
NOISE_SCORE_MIN = 10.0  # Minimum composite score average for filtering weak bursts
MERGE_GAP = timedelta(minutes=10)  # Merge intervals closer than this
debug_dir = '../data/debug_scores'
os.makedirs(debug_dir, exist_ok=True)

# Weights for composite score
weights = {
    'proton_bulk_speed': 1.0,
    'proton_density': 1.0,
    'composite_flux': 1.0,
    'proton_thermal': 0.5,
    'proton_xvelocity': 0.5,
    'proton_yvelocity': 0.5,
    'proton_zvelocity': 0.5,
    'alpha_proton_ratio': 0.7,
    'velocity_magnitude': 0.7
}

params = list(weights.keys())
print("\n🚀 Starting Halo CME Detection...\n")
detected_events = []

for _, row in catalog.iterrows():
    print(f"🔍 Processing CME {row['CME_Number']}...")

    cme_start = row['Expected_Start']
    cme_end = row['Expected_End']
    window_start = cme_start - timedelta(hours=48)
    window_end = cme_end + timedelta(hours=48)
    
    data_window = swis_data[(swis_data['Time'] >= window_start) & (swis_data['Time'] <= window_end)].copy()
    if data_window.empty:
        print("⚠️ No SWIS data found in this window.")
        continue

    composite_score = pd.Series(0, index=data_window.index)

    for param in params:
        if param not in data_window.columns:
            print(f"⚠️ Parameter {param} not found in data.")
            continue

        data_window[f'{param}_mean'] = data_window[param].rolling(window=ROLLING_WINDOW, min_periods=1).mean()
        data_window[f'{param}_std'] = data_window[param].rolling(window=ROLLING_WINDOW, min_periods=1).std()
        data_window[f'{param}_std'] = data_window[f'{param}_std'].replace(0, 1e-6)

        z_scores = (data_window[param] - data_window[f'{param}_mean']) / data_window[f'{param}_std']
        z_scores = z_scores.clip(lower=0)

        adaptive_threshold = max(COMPOSITE_THRESHOLD_MIN, np.percentile(z_scores.dropna(), PERCENTILE_THRESHOLD))
        score_contrib = weights[param] * (z_scores > adaptive_threshold) * z_scores
        composite_score += score_contrib.fillna(0)

    data_window['Composite_Score'] = composite_score

    # Save debug
    data_window[['Time', 'Composite_Score']].to_csv(os.path.join(debug_dir, f"CME_{row['CME_Number']}_scores.csv"), index=False)

    threshold = np.percentile(composite_score.dropna(), PERCENTILE_THRESHOLD)
    print(f"\n📊 Composite Score Summary for CME {row['CME_Number']}")
    print(data_window['Composite_Score'].describe())
    print(f"🎯 {PERCENTILE_THRESHOLD}th Percentile Threshold: {threshold:.2f}")

    data_window['High_Score'] = data_window['Composite_Score'] > threshold
    data_window['Group'] = (data_window['High_Score'] != data_window['High_Score'].shift()).cumsum()

    candidate_events = []
    for _, group_df in data_window.groupby('Group'):
        if not group_df['High_Score'].iloc[0]:
            continue

        start_time = group_df['Time'].iloc[0]
        end_time = group_df['Time'].iloc[-1]
        duration = end_time - start_time
        avg_score = group_df['Composite_Score'].mean()

        if avg_score >= NOISE_SCORE_MIN:
            candidate_events.append((start_time, end_time, avg_score))

    # Merge nearby intervals
    merged_events = []
    for event in sorted(candidate_events):
        if not merged_events:
            merged_events.append(list(event))
        else:
            last = merged_events[-1]
            if event[0] - last[1] <= MERGE_GAP:
                last[1] = event[1]
                last[2] = max(last[2], event[2])
            else:
                merged_events.append(list(event))

    if merged_events:
        print(f"✅ Detected {len(merged_events)} merged event(s) in this window.")
        for start, end, score in merged_events:
            # Categorize CME strength
            if score > 100:
                strength = "Strong"
            elif score > 30:
                strength = "Moderate"
            else:
                strength = "Weak"

            detected_events.append({
                'CME_Number': row['CME_Number'],
                'Detected_Start': start,
                'Detected_End': end,
                'Avg_Score': round(score, 2),
                'Strength': strength
            })
    else:
        print("⚠️ No Halo CME detected in this window.")

# Save results
if detected_events:
    detected_df = pd.DataFrame(detected_events)
    detected_df.to_csv('../data/detected_halo_cmes.csv', index=False)
    print("\n🎯 Detection completed. Results saved to '../data/detected_halo_cmes.csv'.")
else:
    print("\n⚠️ No Halo CME detected in the dataset.")

print("\n✅ Detection completed.")
