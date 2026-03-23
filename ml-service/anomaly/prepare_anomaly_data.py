import os
import json
import numpy as np
import pandas as pd
from colorama import init, Fore

init(autoreset=True)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

ROUTE_MAP = {"oral": 0, "iv": 1, "topical": 2, "inhaled": 3, "sublingual": 4}

# ── Load data ─────────────────────────────────────────────────────────────────
print(Fore.YELLOW + "  Loading data files...")

with open(os.path.join(DATA_DIR, "augmented_prescriptions.json"), encoding="utf-8") as f:
    prescriptions = json.load(f)

with open(os.path.join(DATA_DIR, "patients.json"), encoding="utf-8") as f:
    patients = {p["patient_id"]: p for p in json.load(f)}

formulary_df = pd.read_csv(os.path.join(DATA_DIR, "drug_formulary.csv"))
formulary = {
    str(row["drug_name"]).strip().lower(): float(row["normal_dose_mg"] or 0)
    for _, row in formulary_df.iterrows()
}

print(Fore.YELLOW + f"  Prescriptions: {len(prescriptions)} | "
      f"Patients: {len(patients)} | Formulary drugs: {len(formulary)}")

# ── Collect normal dosage samples (no DOSAGE_ERROR) ───────────────────────────
print(Fore.YELLOW + "  Extracting normal dosage samples...")

rows = []

for rx in prescriptions:
    error_types = rx.get("error_types", []) or []
    if "DOSAGE_ERROR" in error_types:
        continue                    # skip — these are the anomalies

    patient    = patients.get(rx.get("patient_id"), {})
    patient_age    = int(patient.get("age", 0))
    patient_weight = float(patient.get("weight_kg", 0.0))

    for drug in rx.get("prescribed_drugs", []):
        drug_name  = str(drug.get("drug_name", "")).strip()
        drug_lower = drug_name.lower()

        prescribed_dose_mg = float(drug.get("dose_mg", 0) or 0)
        normal_dose_mg     = formulary.get(drug_lower, 0.0)
        dose_ratio         = (
            prescribed_dose_mg / normal_dose_mg
            if normal_dose_mg > 0 else 1.0
        )
        duration_days  = int(drug.get("duration_days", 7) or 7)
        route_encoded  = ROUTE_MAP.get(
            str(drug.get("route", "oral")).strip().lower(), 5
        )

        rows.append({
            "drug_name":           drug_lower,
            "prescribed_dose_mg":  prescribed_dose_mg,
            "normal_dose_mg":      normal_dose_mg,
            "dose_ratio":          dose_ratio,
            "patient_age":         patient_age,
            "patient_weight":      patient_weight,
            "duration_days":       duration_days,
            "route_encoded":       route_encoded,
        })

df = pd.DataFrame(rows)
print(Fore.YELLOW + f"  Total raw samples: {len(df)}")

# ── Filter to drugs with >= 20 samples ────────────────────────────────────────
drug_counts = df["drug_name"].value_counts()
eligible    = drug_counts[drug_counts >= 20].index
df_filtered = df[df["drug_name"].isin(eligible)].copy()
df_filtered = df_filtered.dropna()

# ── Build per-drug profiles ───────────────────────────────────────────────────
profiles = {}
for drug, grp in df_filtered.groupby("drug_name"):
    doses = grp["prescribed_dose_mg"]
    profiles[drug] = {
        "mean_dose":                    round(float(doses.mean()), 4),
        "std_dose":                     round(float(doses.std()), 4),
        "min_dose":                     round(float(doses.min()), 4),
        "max_dose":                     round(float(doses.max()), 4),
        "sample_count":                 int(len(grp)),
        "normal_dose_from_formulary":   float(formulary.get(drug, 0.0)),
    }

# ── Save outputs ──────────────────────────────────────────────────────────────
profiles_path = os.path.join(DATA_DIR, "anomaly_profiles.json")
with open(profiles_path, "w", encoding="utf-8") as f:
    json.dump(profiles, f, indent=2)

training_path = os.path.join(DATA_DIR, "anomaly_training_data.csv")
df_filtered.to_csv(training_path, index=False)

# ── Summary ───────────────────────────────────────────────────────────────────
print(Fore.GREEN + f"\n✅ Anomaly profiles built for {len(profiles)} drugs")
print(Fore.GREEN + f"📊 Total normal samples: {len(df_filtered)}")

top5 = (
    df_filtered.groupby("drug_name")
    .size()
    .nlargest(5)
    .reset_index(name="count")
)
print(Fore.CYAN + "\nTop 5 drugs by sample count:")
print(f"  {'Drug':<28} {'Samples':>8}")
print(f"  {'-'*28} {'-'*8}")
for _, row in top5.iterrows():
    print(f"  {row['drug_name']:<28} {row['count']:>8}")
