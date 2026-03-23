import os
import json
import joblib
import numpy as np
import pandas as pd
from colorama import init, Fore
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

init(autoreset=True)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

# ── STEP 1: Load all data ─────────────────────────────────────────────────────
print(Fore.YELLOW + "  Loading data files...")

with open(os.path.join(DATA_DIR, "patients.json"), encoding="utf-8") as f:
    patients_list = json.load(f)
patients = {p["patient_id"]: p for p in patients_list}

with open(os.path.join(DATA_DIR, "augmented_prescriptions.json"), encoding="utf-8") as f:
    prescriptions = json.load(f)

formulary_df = pd.read_csv(os.path.join(DATA_DIR, "drug_formulary.csv"))
formulary = {
    row["drug_name"].strip().lower(): row
    for _, row in formulary_df.iterrows()
}

diag_map_df = pd.read_csv(os.path.join(DATA_DIR, "diagnosis_drug_map.csv"))
diag_map = {
    row["diagnosis"].strip().lower(): {
        "appropriate": [
            d.strip().lower()
            for d in str(row["appropriate_drugs"]).split("|")
        ],
        "inappropriate": [
            d.strip().lower()
            for d in str(row["inappropriate_drugs_example"]).split("|")
        ],
    }
    for _, row in diag_map_df.iterrows()
}

print(Fore.YELLOW + f"  Patients: {len(patients)} | Prescriptions: {len(prescriptions)}"
      f" | Formulary: {len(formulary)} | Diag map: {len(diag_map)}")

# ── STEP 2: Fit LabelEncoder on all known drug classes ────────────────────────
all_drug_classes = (
    formulary_df["drug_class"]
    .dropna()
    .str.strip()
    .unique()
    .tolist()
)
le = LabelEncoder()
le.fit(all_drug_classes)

ROUTE_MAP = {
    "oral":       0,
    "iv":         1,
    "topical":    2,
    "inhaled":    3,
    "sublingual": 4,
}

# ── STEP 3: Build training samples ────────────────────────────────────────────
print(Fore.YELLOW + "  Building feature matrix...")

rows = []

for rx in prescriptions:
    patient_id = rx.get("patient_id")
    patient    = patients.get(patient_id)
    if patient is None:
        continue

    error_types      = rx.get("error_types", []) or []
    num_drugs_in_rx  = len(rx.get("prescribed_drugs", []))

    for drug in rx.get("prescribed_drugs", []):
        drug_name  = drug.get("drug_name", "").strip()
        drug_lower = drug_name.lower()

        # ── Numerical features ────────────────────────────────────────────────
        patient_age      = int(patient.get("age", 0))
        patient_weight   = float(patient.get("weight_kg", 0.0))
        is_male          = 1 if patient.get("gender", "") == "Male" else 0
        num_diagnoses    = len(patient.get("diagnosis", []))
        num_current_meds = len(patient.get("current_medications", []))
        num_allergies    = len(patient.get("allergies", []))

        formulary_entry  = formulary.get(drug_lower)
        normal_dose_mg   = (
            float(formulary_entry["normal_dose_mg"])
            if formulary_entry is not None
            else 0.0
        )
        prescribed_dose_mg = float(drug.get("dose_mg", 0) or 0)
        dose_ratio = (
            prescribed_dose_mg / normal_dose_mg
            if normal_dose_mg > 0
            else 1.0
        )

        # ── Categorical features ──────────────────────────────────────────────
        if formulary_entry is not None:
            drug_class = str(formulary_entry["drug_class"]).strip()
            if drug_class in le.classes_:
                drug_class_encoded = int(le.transform([drug_class])[0])
            else:
                drug_class_encoded = -1
        else:
            drug_class_encoded = -1

        route_raw          = str(drug.get("route", "")).strip().lower()
        drug_route_encoded = ROUTE_MAP.get(route_raw, 5)   # unknown → other=5

        # ── Binary features ───────────────────────────────────────────────────
        patient_diagnoses = [d.lower() for d in patient.get("diagnosis", [])]

        drug_matches_any_diagnosis = 0
        drug_is_inappropriate      = 0

        for diag in patient_diagnoses:
            entry = diag_map.get(diag)
            if entry is None:
                continue
            if drug_lower in entry["appropriate"]:
                drug_matches_any_diagnosis = 1
            if drug_lower in entry["inappropriate"]:
                drug_is_inappropriate = 1

        comorbidities  = patient.get("comorbidities", []) or []
        has_comorbidity = 1 if len(comorbidities) > 0 else 0

        # ── Label ─────────────────────────────────────────────────────────────
        label = 1 if "INDICATION_MISMATCH" in error_types else 0

        rows.append({
            "patient_age":               patient_age,
            "patient_weight":            patient_weight,
            "is_male":                   is_male,
            "num_diagnoses":             num_diagnoses,
            "num_current_meds":          num_current_meds,
            "num_allergies":             num_allergies,
            "normal_dose_mg":            normal_dose_mg,
            "prescribed_dose_mg":        prescribed_dose_mg,
            "dose_ratio":                dose_ratio,
            "num_drugs_in_rx":           num_drugs_in_rx,
            "drug_class_encoded":        drug_class_encoded,
            "drug_route_encoded":        drug_route_encoded,
            "drug_matches_any_diagnosis": drug_matches_any_diagnosis,
            "drug_is_inappropriate":     drug_is_inappropriate,
            "has_comorbidity":           has_comorbidity,
            "label":                     label,
        })

# ── STEP 4: Build DataFrame ───────────────────────────────────────────────────
feature_columns = [
    "patient_age", "patient_weight", "is_male",
    "num_diagnoses", "num_current_meds", "num_allergies",
    "normal_dose_mg", "prescribed_dose_mg", "dose_ratio",
    "num_drugs_in_rx", "drug_class_encoded", "drug_route_encoded",
    "drug_matches_any_diagnosis", "drug_is_inappropriate", "has_comorbidity",
]

df = pd.DataFrame(rows, columns=feature_columns + ["label"])
df = df.dropna()

n0 = int((df["label"] == 0).sum())
n1 = int((df["label"] == 1).sum())
print(Fore.CYAN + f"  Label 0 (correct): {n0} samples")
print(Fore.CYAN + f"  Label 1 (mismatch): {n1} samples")

# ── STEP 5: Train / Val / Test split ─────────────────────────────────────────
X = df[feature_columns]
y = df["label"]

X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# val_size as fraction of the original total → adjust for the reduced set
val_fraction_of_trainval = 0.15 / 0.80   # ≈ 0.1875

X_train, X_val, y_train, y_val = train_test_split(
    X_train_val, y_train_val,
    test_size=val_fraction_of_trainval,
    random_state=42,
    stratify=y_train_val,
)

# ── STEP 6: Save ──────────────────────────────────────────────────────────────
train_df = X_train.copy(); train_df["label"] = y_train.values
val_df   = X_val.copy();   val_df["label"]   = y_val.values
test_df  = X_test.copy();  test_df["label"]  = y_test.values

train_df.to_csv(os.path.join(DATA_DIR, "classifier_train.csv"), index=False)
val_df.to_csv(  os.path.join(DATA_DIR, "classifier_val.csv"),   index=False)
test_df.to_csv( os.path.join(DATA_DIR, "classifier_test.csv"),  index=False)

joblib.dump(le, os.path.join(DATA_DIR, "classifier_label_encoder.joblib"))

with open(os.path.join(DATA_DIR, "classifier_feature_columns.json"), "w", encoding="utf-8") as f:
    json.dump(feature_columns, f, indent=2)

total = len(df)
pct0  = 100 * n0 / total
pct1  = 100 * n1 / total

print(Fore.GREEN + "\n✅ Classifier data prepared")
print(Fore.GREEN + f"📊 Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")
print(Fore.GREEN + f"⚖️  Class balance — 0: {pct0:.1f}% | 1: {pct1:.1f}%")
