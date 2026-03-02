import os
import json
import joblib
import numpy as np

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SAVE_DIR = os.path.join(BASE_DIR, "saved_model")

# ── SECTION 1: Lazy model loading ─────────────────────────────────────────────
_model    = None
_scaler   = None
_profiles = None

ROUTE_MAP = {"oral": 0, "iv": 1, "topical": 2, "inhaled": 3, "sublingual": 4}


def load_anomaly_model():
    global _model, _scaler, _profiles

    if _model is not None:
        return

    _model  = joblib.load(os.path.join(SAVE_DIR, "anomaly_model.joblib"))
    _scaler = joblib.load(os.path.join(SAVE_DIR, "anomaly_scaler.joblib"))

    with open(os.path.join(DATA_DIR, "anomaly_profiles.json"), encoding="utf-8") as f:
        _profiles = json.load(f)

    print("✅ Anomaly model loaded")


# ── SECTION 2: Core inference function ────────────────────────────────────────
def check_dosage_anomaly(
    drug_name: str,
    prescribed_dose_mg: float,
    patient_age: int,
    patient_weight: float,
    duration_days: int = 7,
    route: str = "oral",
) -> dict:
    load_anomaly_model()

    drug_lower = drug_name.strip().lower()
    profile    = _profiles.get(drug_lower)

    normal_dose = (
        float(profile["normal_dose_from_formulary"])
        if profile is not None
        else 0.0
    )
    dose_ratio = (
        prescribed_dose_mg / normal_dose if normal_dose > 0 else 1.0
    )

    route_encoded = ROUTE_MAP.get(route.strip().lower(), 5)

    features = [[
        prescribed_dose_mg,
        normal_dose,
        dose_ratio,
        float(patient_age),
        float(patient_weight),
        float(duration_days),
        float(route_encoded),
    ]]

    scaled     = _scaler.transform(features)
    prediction = _model.predict(scaled)[0]          # 1 = normal, -1 = anomaly
    score      = _model.decision_function(scaled)[0]  # higher = more normal

    # ── Severity ───────────────────────────────────────────────────────────────
    if prediction == -1:
        if dose_ratio > 5 or dose_ratio < 0.1:
            severity = "CRITICAL"
        elif dose_ratio > 3 or dose_ratio < 0.2:
            severity = "HIGH"
        else:
            severity = "MEDIUM"
        message = f"Dose is {dose_ratio:.1f}x the normal dose"
    else:
        severity = "NORMAL"
        message  = "Dose is within normal range"

    return {
        "drug_name":           drug_name,
        "prescribed_dose_mg":  prescribed_dose_mg,
        "normal_dose_mg":      normal_dose,
        "dose_ratio":          round(dose_ratio, 3),
        "is_anomaly":          bool(prediction == -1),
        "anomaly_score":       round(float(score), 4),
        "severity":            severity,
        "message":             message,
    }


# ── SECTION 3: Test block ──────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        ("Metformin", 500,  55, 75, 30, "oral",  "NORMAL   (500 mg is standard)"),
        ("Metformin", 5000, 55, 75, 30, "oral",  "CRITICAL (10x normal)"),
        ("Aspirin",   75,   60, 70,  7, "oral",  "NORMAL   (75 mg is standard)"),
        ("Aspirin",   750,  60, 70,  7, "oral",  "ANOMALY  (10x normal)"),
    ]

    for drug, dose, age, weight, days, route, expected in test_cases:
        result = check_dosage_anomaly(drug, dose, age, weight, days, route)
        print(f"─── {drug} {dose} mg ───────────────────────────────────────")
        print(f"  Normal dose     : {result['normal_dose_mg']} mg")
        print(f"  Dose ratio      : {result['dose_ratio']}x")
        print(f"  Is anomaly      : {result['is_anomaly']}   (expected: {expected})")
        print(f"  Severity        : {result['severity']}")
        print(f"  Anomaly score   : {result['anomaly_score']}")
        print(f"  Message         : {result['message']}")
        print()
