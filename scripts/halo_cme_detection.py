# Updated Detection Script (halo_cme_detection.py) with Confidence, Strength Refinement, Deduplication, and CACTus Validation

import pandas as pd
import numpy as np
from datetime import timedelta
import os

# Load dataset
swis_data = pd.read_csv('../data/final_dataset.csv', parse_dates=['Time'])
catalog = pd.read_csv('../data/cactus/halo_cmes.csv', parse_dates=['Launch_Time', 'Expected_Start', 'Expected_End'])

# Set parameters
ROLLING_WINDOW = 15
PERCENTILE_THRESHOLD = 90
COMPOSITE_THRESHOLD_MIN = 2.0
MERGE_GAP = timedelta(minutes=10)
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
detected_cme_ids = set()

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
        z_scores = z_scores.clip(lower=0, upper=10)

        adaptive_threshold = max(COMPOSITE_THRESHOLD_MIN, np.percentile(z_scores.dropna(), PERCENTILE_THRESHOLD))
        score_contrib = weights[param] * (z_scores > adaptive_threshold) * z_scores
        composite_score += score_contrib.fillna(0)

    data_window['Composite_Score'] = composite_score
    data_window[['Time', 'Composite_Score']].to_csv(os.path.join(debug_dir, f"CME_{row['CME_Number']}_scores.csv"), index=False)

    nonzero_scores = composite_score[composite_score > 0]
    max_score = composite_score.max()

    if not nonzero_scores.empty:
        threshold = np.percentile(nonzero_scores, PERCENTILE_THRESHOLD)
        if threshold > 0.6 * max_score:
            print(f"⚠️ Threshold {threshold:.2f} too high relative to max {max_score:.2f}. Lowering for sensitivity.")
            threshold = max(COMPOSITE_THRESHOLD_MIN, max_score * 0.3)
    else:
        threshold = COMPOSITE_THRESHOLD_MIN

    NOISE_SCORE_MIN = max(3.0, threshold * 0.4)
    MIN_DURATION = timedelta(minutes=2)

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
        peak_score = group_df['Composite_Score'].max()

        if avg_score >= NOISE_SCORE_MIN and duration >= MIN_DURATION:
            confidence = round((avg_score / max_score) * 100, 1) if max_score > 0 else 0.0
            candidate_events.append((start_time, end_time, avg_score, peak_score, duration.total_seconds() / 60, confidence))

    merged_events = []
    for event in sorted(candidate_events):
        if not merged_events:
            merged_events.append(list(event))
        else:
            last = merged_events[-1]
            if event[0] - last[1] <= MERGE_GAP:
                last[1] = event[1]
                last[2] = max(last[2], event[2])
                last[3] = max(last[3], event[3])
                last[4] += event[4]
                last[5] = max(last[5], event[5])
            else:
                merged_events.append(list(event))

    if merged_events:
        print(f"✅ Detected {len(merged_events)} merged event(s) in this window.")
        for start, end, score, peak, duration_mins, confidence in merged_events:
            if peak > 100 or score > 80:
                strength = "Strong"
            elif peak > 40 or score > 30:
                strength = "Moderate"
            else:
                strength = "Weak"

            valid = 'TP' if (end >= row['Expected_Start']) and (start <= row['Expected_End']) else 'FP'
            detected_events.append({
                'CME_Number': row['CME_Number'],
                'Detected_Start': start,
                'Detected_End': end,
                'Avg_Score': round(score, 2),
                'Peak_Score': round(peak, 2),
                'Duration_mins': round(duration_mins, 2),
                'Confidence': f"{confidence}%",
                'Strength': strength,
                'Validation': valid
            })
    else:
        print("⚠️ No Halo CME detected in this window.")

# Evaluation metrics
TP = sum(1 for e in detected_events if e['Validation'] == 'TP')
FP = sum(1 for e in detected_events if e['Validation'] == 'FP')
FN = 0
for _, row in catalog.iterrows():
    overlaps = any((e['Detected_End'] >= row['Expected_Start']) and (e['Detected_Start'] <= row['Expected_End']) for e in detected_events)
    if not overlaps:
        FN += 1

precision = TP / (TP + FP) if TP + FP > 0 else 0
recall = TP / (TP + FN) if TP + FN > 0 else 0
f1_score = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0

# Save outputs
if detected_events:
    detected_df = pd.DataFrame(detected_events)
    detected_df.drop_duplicates(subset=['Detected_Start', 'Detected_End'], inplace=True)
    detected_df.to_csv('../data/detected_halo_cmes.csv', index=False)

    with open('../data/evaluation_metrics.txt', 'w') as f:
        f.write("Precision: {:.2f}\n".format(precision))
        f.write("Recall: {:.2f}\n".format(recall))
        f.write("F1 Score: {:.2f}\n".format(f1_score))
        f.write("True Positives: {}\n".format(TP))
        f.write("False Positives: {}\n".format(FP))
        f.write("False Negatives: {}\n".format(FN))

    print("\n📁 Evaluation metrics saved to '../data/evaluation_metrics.txt'.")
    print("\n🎯 Detection completed. Results saved to '../data/detected_halo_cmes.csv'.")
else:
    print("\n⚠️ No Halo CME detected in the dataset.")

print("\n✅ Detection completed.")
