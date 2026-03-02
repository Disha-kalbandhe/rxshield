import os
import json
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SAVE_DIR = os.path.join(BASE_DIR, "saved_model")

# ── SECTION 1: Lazy model loading ─────────────────────────────────────────────
_model           = None
_scaler          = None
_formulary       = None
_diag_map        = None
_feature_columns = None
_label_encoder   = None

ROUTE_MAP = {
    "oral":       0,
    "iv":         1,
    "topical":    2,
    "inhaled":    3,
    "sublingual": 4,
}


def load_classifier_model():
    global _model, _scaler, _formulary, _diag_map, _feature_columns, _label_encoder

    if _model is not None:
        return

    _model  = joblib.load(os.path.join(SAVE_DIR, "classifier_model.joblib"))
    _scaler = joblib.load(os.path.join(SAVE_DIR, "classifier_scaler.joblib"))

    with open(os.path.join(DATA_DIR, "classifier_feature_columns.json"),
              encoding="utf-8") as f:
        _feature_columns = json.load(f)

    _label_encoder = joblib.load(
        os.path.join(DATA_DIR, "classifier_label_encoder.joblib")
    )

    # Load formulary → keyed by lowercase drug name
    formulary_df = pd.read_csv(os.path.join(DATA_DIR, "drug_formulary.csv"))
    _formulary = {
        str(row["drug_name"]).strip().lower(): row.to_dict()
        for _, row in formulary_df.iterrows()
    }

    # Load diagnosis map → keyed by lowercase diagnosis
    diag_df = pd.read_csv(os.path.join(DATA_DIR, "diagnosis_drug_map.csv"))
    _diag_map = {
        str(row["diagnosis"]).strip().lower(): {
            "appropriate": [
                d.strip().lower()
                for d in str(row["appropriate_drugs"]).split("|")
            ],
            "inappropriate": [
                d.strip().lower()
                for d in str(row["inappropriate_drugs_example"]).split("|")
            ],
        }
        for _, row in diag_df.iterrows()
    }

    print("✅ Classifier model loaded")


# ── SECTION 2: Core inference function ────────────────────────────────────────
def check_indication_mismatch(drug_name: str, patient_data: dict) -> dict:
    """
    patient_data = {
      "age": int, "gender": str, "weight_kg": float,
      "diagnosis": list, "allergies": list,
      "current_medications": list, "comorbidities": list
    }
    """
    load_classifier_model()

    drug_lower = drug_name.strip().lower()
    drug_info  = _formulary.get(drug_lower, {})

    # ── Numerical features ─────────────────────────────────────────────────────
    patient_age       = int(patient_data.get("age", 0))
    patient_weight    = float(patient_data.get("weight_kg", 0.0))
    is_male           = 1 if patient_data.get("gender", "") == "Male" else 0
    num_diagnoses     = len(patient_data.get("diagnosis", []))
    num_current_meds  = len(patient_data.get("current_medications", []))
    num_allergies     = len(patient_data.get("allergies", []))

    normal_dose_mg     = float(drug_info.get("normal_dose_mg", 0) or 0)
    # Use normal dose as proxy for prescribed dose when not explicitly given
    prescribed_dose_mg = float(patient_data.get("dose_mg", normal_dose_mg) or normal_dose_mg)
    dose_ratio         = (
        prescribed_dose_mg / normal_dose_mg if normal_dose_mg > 0 else 1.0
    )
    num_drugs_in_rx    = int(patient_data.get("num_drugs_in_rx", 1))

    # ── Categorical features ───────────────────────────────────────────────────
    drug_class = str(drug_info.get("drug_class", "")).strip()
    if drug_class and _label_encoder is not None and drug_class in _label_encoder.classes_:
        drug_class_encoded = int(_label_encoder.transform([drug_class])[0])
    else:
        drug_class_encoded = -1     # matches training sentinel for unknown drugs

    route_raw          = str(patient_data.get("route", "oral")).strip().lower()
    drug_route_encoded = ROUTE_MAP.get(route_raw, 5)   # unknown → other=5

    # ── Binary features ────────────────────────────────────────────────────────
    patient_diagnoses = [d.lower() for d in patient_data.get("diagnosis", [])]

    drug_matches_any_diagnosis = 0
    drug_is_inappropriate      = 0

    for diag in patient_diagnoses:
        entry = _diag_map.get(diag)
        if entry is None:
            continue
        if drug_lower in entry["appropriate"]:
            drug_matches_any_diagnosis = 1
        if drug_lower in entry["inappropriate"]:
            drug_is_inappropriate = 1

    comorbidities   = patient_data.get("comorbidities", []) or []
    has_comorbidity = 1 if len(comorbidities) > 0 else 0

    # ── Assemble feature vector in training order ──────────────────────────────
    feature_values = {
        "patient_age":                patient_age,
        "patient_weight":             patient_weight,
        "is_male":                    is_male,
        "num_diagnoses":              num_diagnoses,
        "num_current_meds":           num_current_meds,
        "num_allergies":              num_allergies,
        "normal_dose_mg":             normal_dose_mg,
        "prescribed_dose_mg":         prescribed_dose_mg,
        "dose_ratio":                 dose_ratio,
        "num_drugs_in_rx":            num_drugs_in_rx,
        "drug_class_encoded":         drug_class_encoded,
        "drug_route_encoded":         drug_route_encoded,
        "drug_matches_any_diagnosis": drug_matches_any_diagnosis,
        "drug_is_inappropriate":      drug_is_inappropriate,
        "has_comorbidity":            has_comorbidity,
    }

    features_array = np.array(
        [[feature_values[col] for col in _feature_columns]], dtype=float
    )
    features_scaled = _scaler.transform(features_array)

    prediction  = _model.predict(features_scaled)[0]
    probability = _model.predict_proba(features_scaled)[0][1]

    risk_level = (
        "HIGH"   if probability > 0.8 else
        "MEDIUM" if probability > 0.5 else
        "LOW"
    )

    return {
        "drug_name":          drug_name,
        "is_mismatch":        bool(prediction == 1),
        "confidence":         round(float(probability), 4),
        "patient_diagnoses":  patient_data.get("diagnosis", []),
        "drug_class":         drug_info.get("drug_class", "unknown"),
        "drug_indications":   drug_info.get("indications", "unknown"),
        "risk_level":         risk_level,
    }


# ── SECTION 3: Batch function ──────────────────────────────────────────────────
def check_all_drugs(drugs: list, patient_data: dict) -> list:
    """
    Run check_indication_mismatch for every drug in the list.
    Returns only results where is_mismatch is True OR confidence > 0.4
    (captures confirmed mismatches and borderline cases).
    """
    results = [check_indication_mismatch(drug, patient_data) for drug in drugs]
    return [r for r in results if r["is_mismatch"] or r["confidence"] > 0.4]


# ── SECTION 4: Test block ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test case 1 — correct match (Metformin for Type 2 Diabetes)
    result1 = check_indication_mismatch("Metformin", {
        "age": 55, "gender": "Male", "weight_kg": 75,
        "diagnosis": ["Type 2 Diabetes"], "allergies": [],
        "current_medications": [], "comorbidities": [],
    })
    print("─── Test 1: Correct match ───────────────────────────")
    print(f"  Drug            : {result1['drug_name']}")
    print(f"  Diagnoses       : {result1['patient_diagnoses']}")
    print(f"  Drug class      : {result1['drug_class']}")
    print(f"  Indications     : {result1['drug_indications']}")
    print(f"  Is mismatch     : {result1['is_mismatch']}   (expected: False)")
    print(f"  Confidence      : {result1['confidence']}")
    print(f"  Risk level      : {result1['risk_level']}")

    print()

    # Test case 2 — wrong drug for diagnosis (Furosemide for Type 2 Diabetes)
    result2 = check_indication_mismatch("Furosemide", {
        "age": 45, "gender": "Female", "weight_kg": 65,
        "diagnosis": ["Type 2 Diabetes"], "allergies": [],
        "current_medications": [], "comorbidities": [],
    })
    print("─── Test 2: Indication mismatch ─────────────────────")
    print(f"  Drug            : {result2['drug_name']}")
    print(f"  Diagnoses       : {result2['patient_diagnoses']}")
    print(f"  Drug class      : {result2['drug_class']}")
    print(f"  Indications     : {result2['drug_indications']}")
    print(f"  Is mismatch     : {result2['is_mismatch']}   (expected: True)")
    print(f"  Confidence      : {result2['confidence']}")
    print(f"  Risk level      : {result2['risk_level']}")
