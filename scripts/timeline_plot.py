import pandas as pd
import matplotlib.pyplot as plt
import os

DETECTED_PATH = '../data/detected_halo_cmes.csv'
PLOT_DIR = '../plots'
os.makedirs(PLOT_DIR, exist_ok=True)

df = pd.read_csv(DETECTED_PATH, parse_dates=['Detected_Start', 'Detected_End'])
cme_numbers = df['CME_Number'].unique()

for cme_num in cme_numbers:
    cme_df = df[df['CME_Number'] == cme_num]
    if cme_df.empty:
        continue
    fig, ax = plt.subplots(figsize=(12, 2 + 0.5 * len(cme_df)))
    for i, row in cme_df.iterrows():
        ax.plot([row['Detected_Start'], row['Detected_End']], [i, i], linewidth=10, color='#008080', solid_capstyle='round')
        ax.scatter([row['Detected_Start'], row['Detected_End']], [i, i], color='#005050', s=40, zorder=3)

    ax.set_yticks(range(len(cme_df)))
    ax.set_yticklabels([f'Event {i+1}' for i in range(len(cme_df))], fontsize=11)
    ax.set_title(f'Detected Events Timeline – CME {cme_num}', fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel('Time', fontsize=12)
    ax.set_xlim([cme_df['Detected_Start'].min() - pd.Timedelta(hours=1), cme_df['Detected_End'].max() + pd.Timedelta(hours=1)])
    ax.tick_params(axis='x', labelsize=10, rotation=30)
    ax.tick_params(axis='y', labelsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)
    plt.tight_layout()

    output_path = os.path.join(PLOT_DIR, f"cme_{cme_num}_timeline.png")
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"✅ Saved: {output_path}")
