import pandas as pd
import matplotlib.pyplot as plt
import os

CME_NUMBER = 12
DETECTED_PATH = '../data/detected_halo_cmes.csv'
PLOT_DIR = '../plots'

df = pd.read_csv(DETECTED_PATH, parse_dates=['Detected_Start', 'Detected_End'])
df = df[df['CME_Number'] == CME_NUMBER]

fig, ax = plt.subplots(figsize=(10, 4))
for i, row in df.iterrows():
    ax.plot([row['Detected_Start'], row['Detected_End']], [i, i], linewidth=5, color='teal')

ax.set_yticks(range(len(df)))
ax.set_yticklabels([f'Event {i+1}' for i in range(len(df))])
ax.set_title(f'Detected Events Timeline – CME {CME_NUMBER}')
ax.set_xlabel('Time')
ax.grid(True)
plt.tight_layout()

output_path = os.path.join(PLOT_DIR, f"cme_{CME_NUMBER}_timeline.png")
plt.savefig(output_path)
plt.show()

print(f"✅ Saved: {output_path}")
