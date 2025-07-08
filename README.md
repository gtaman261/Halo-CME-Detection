# ☀️ Halo CME Detection using Aditya-L1 SWIS-ASPEX Data

This project focuses on detecting **Halo Coronal Mass Ejections (CMEs)** using **particle flux data from the SWIS-ASPEX payload** onboard **ISRO's Aditya-L1 mission**. It aligns and analyzes in-situ measurements to flag potential CME events and validates them against the **CACTus Halo CME catalog**.

---

## 📌 Problem Statement (PS-10)

> Identify Halo CME Events Based on Particle Data from SWIS-ASPEX Payload onboard Aditya-L1

Sudden changes in solar wind particle flux can indicate CME activity. Early detection enables **timely space weather alerts**, crucial for protecting satellites, communication systems, power infrastructure, and other space assets.

---

## 🧠 Our Approach

### 🔹 Data Sources
- **SWIS-ASPEX Level-2 CDF files** (Bulk, TH1, TH2)
- **CACTus Halo CME Catalog** (for validation)

### 🔹 Key Parameters Considered
- `proton_bulk_speed`, `proton_density`, `proton_thermal`
- `composite_flux`, `alpha_proton_ratio`
- `proton_xvelocity`, `yvelocity`, `zvelocity`
- `velocity_magnitude`

### 🔹 Detection Pipeline
1. **CDF → CSV conversion** using `spacepy`
2. **Data Cleaning & Merging** into a unified dataset
3. **Composite Scoring** using rolling z-scores with weighted parameters
4. **Anomaly Detection** via adaptive percentile thresholds
5. **Noise Filtering** to eliminate weak/noisy bursts
6. **Interval Merging** for temporally close events
7. **Strength Categorization** (Weak / Moderate / Strong)
8. **Validation** with CACTus catalog (optional)

---

## 📁 Project Structure

Halo-CME-Detection/
├── data/
│ ├── cactus/ # CACTus Halo CME catalog
│ ├── raw_cdf/ # Original CDF files
│ ├── swis_csv/ # Converted CSVs
│ ├── final_dataset.csv # Cleaned and merged dataset
│ └── detected_halo_cmes.csv # Final detection output
├── plots/ # Generated visualizations
├── scripts/
│ ├── cdf_to_csv.py
│ ├── data_preparation.py
│ ├── halo_cme_detection.py
│ └── visualization.py
├── .gitignore
└── README.md

yaml
Copy
Edit

---

## 🛠️ How to Run

### 1️⃣ Install Requirements

```bash
pip install -r requirements.txt
2️⃣ Convert CDF to CSV
bash
Copy
Edit
python scripts/cdf_to_csv.py
3️⃣ Merge & Prepare Final Dataset
bash
Copy
Edit
python scripts/data_preparation.py
4️⃣ Run CME Detection
bash
Copy
Edit
python scripts/halo_cme_detection.py
5️⃣ Generate Visual Plots
bash
Copy
Edit
python scripts/visualization.py
📊 Visual Outputs
All plots are saved in the plots/ directory:

*_overlay.png: Composite Score with CACTus intervals

*_overlay_with_detected.png: CACTus (orange) vs Detected events (green)

cme_strength_distribution.png: Histogram of CME strengths (Weak/Moderate/Strong)

Example:

<p align="center"> <img src="plots/cme_strength_distribution.png" alt="CME Strength Histogram" width="600"/> </p>
✅ Final Output
📄 detected_halo_cmes.csv: List of detected CME intervals with strength classification

📊 Per-event plots to support interpretation

🧠 Algorithmic detection based on dynamic particle variations

🚀 Highlights
✅ Data-driven, India-centric space solution

🧩 Adaptive z-score thresholding for robust anomaly detection

🔄 Merging logic to prevent over-fragmentation of events

⚙️ Fully scriptable and reproducible workflow

📊 Rich visual and statistical outputs for analysis

🧰 Tools & Libraries Used
pandas, numpy

matplotlib, seaborn

spacepy (for reading CDF files)

scipy, tqdm

📬 Acknowledgements
ISRO Aditya-L1 Mission & SWIS-ASPEX Team

SIDC/CACTus for providing the Halo CME catalog

Bharat Antriksh Hackathon by ISRO & iHUB DivyaSampark

📈 Future Improvements
Add velocity vector direction change analysis

Integrate real-time streaming data support

Develop a web-based dashboard or alert system

Explore machine learning-based trend modeling

