import pandas as pd
import matplotlib.pyplot as plt
import os

# Configuration
CME_NUMBER = 12  # Change as needed
DEBUG_DIR = '../data/debug_scores'
PLOT_DIR = '../plots'
os.makedirs(PLOT_DIR, exist_ok=True)

# Load data
csv_path = os.path.join(DEBUG_DIR, f"CME_{CME_NUMBER}_scores.csv")
df = pd.read_csv(csv_path, parse_dates=['Time'])

# Calculate 90th percentile threshold
threshold = df['Composite_Score'].quantile(0.90)

# Plot composite score
plt.figure(figsize=(12, 5))
plt.plot(df['Time'], df['Composite_Score'], label='Composite Score', color='navy')
plt.axhline(threshold, color='red', linestyle='--', label='90th Percentile Threshold')
plt.title(f'Composite Score Over Time – CME {CME_NUMBER}')
plt.xlabel('Time')
plt.ylabel('Composite Score')
plt.legend()
plt.grid(True)
plt.tight_layout()
output_path = os.path.join(PLOT_DIR, f"cme_{CME_NUMBER}_composite_score.png")
plt.savefig(output_path)
plt.show()

print(f"✅ Saved: {output_path}")
