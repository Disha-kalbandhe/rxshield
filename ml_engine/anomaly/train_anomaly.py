import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from colorama import init, Fore
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

init(autoreset=True)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SAVE_DIR = os.path.join(BASE_DIR, "saved_model")
os.makedirs(SAVE_DIR, exist_ok=True)

FEATURE_COLUMNS = [
    "prescribed_dose_mg", "normal_dose_mg", "dose_ratio",
    "patient_age", "patient_weight", "duration_days", "route_encoded",
]

# ── Load data ─────────────────────────────────────────────────────────────────
print(Fore.YELLOW + "  Loading anomaly training data...")

df = pd.read_csv(os.path.join(DATA_DIR, "anomaly_training_data.csv"))
df = df.dropna(subset=FEATURE_COLUMNS)

with open(os.path.join(DATA_DIR, "anomaly_profiles.json"), encoding="utf-8") as f:
    profiles = json.load(f)

print(Fore.YELLOW + f"  Training samples: {len(df)} across {df['drug_name'].nunique()} drugs")

# ── Scale features ────────────────────────────────────────────────────────────
X = df[FEATURE_COLUMNS].values

scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ── Train Isolation Forest ────────────────────────────────────────────────────
print(Fore.YELLOW + "  Training Isolation Forest (n_estimators=100, contamination=0.05)...")

model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42,
    n_jobs=-1,
)
model.fit(X_scaled)

# ── Evaluate on training data ─────────────────────────────────────────────────
preds    = model.predict(X_scaled)          # 1 = normal, -1 = anomaly
n_flagged = int((preds == -1).sum())
pct       = 100 * n_flagged / len(preds)
print(Fore.CYAN + f"  Normal samples flagged as anomaly: {n_flagged} ({pct:.1f}%)")
print(Fore.CYAN + "  (Expected ~5% at contamination=0.05)")

# ── Save model and scaler ─────────────────────────────────────────────────────
joblib.dump(model,  os.path.join(SAVE_DIR, "anomaly_model.joblib"),  compress=3)
joblib.dump(scaler, os.path.join(SAVE_DIR, "anomaly_scaler.joblib"))

# ── Save metadata ─────────────────────────────────────────────────────────────
metadata = {
    "contamination":    0.05,
    "n_estimators":     100,
    "features":         FEATURE_COLUMNS,
    "trained_at":       datetime.now().isoformat(),
    "training_samples": int(len(df)),
    "drugs_covered":    int(df["drug_name"].nunique()),
}
with open(os.path.join(SAVE_DIR, "anomaly_metadata.json"), "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print(Fore.GREEN + "\n✅ Isolation Forest trained!")
print(Fore.GREEN + f"📊 Training samples: {len(df)}")
print(Fore.GREEN + "📁 Model saved: anomaly/saved_model/")
