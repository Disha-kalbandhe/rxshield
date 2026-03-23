import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from colorama import init, Fore
from sklearn.metrics import (
    classification_report, confusion_matrix,
    f1_score, accuracy_score, roc_auc_score,
)

init(autoreset=True)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SAVE_DIR = os.path.join(BASE_DIR, "saved_model")

# ── Load artifacts ────────────────────────────────────────────────────────────
print(Fore.YELLOW + "  Loading model, scaler and test data...")

with open(os.path.join(DATA_DIR, "classifier_feature_columns.json"), encoding="utf-8") as f:
    feature_columns = json.load(f)

model  = joblib.load(os.path.join(SAVE_DIR, "classifier_model.joblib"))
scaler = joblib.load(os.path.join(SAVE_DIR, "classifier_scaler.joblib"))

test_df = pd.read_csv(os.path.join(DATA_DIR, "classifier_test.csv"))
X_test  = test_df[feature_columns]
y_test  = test_df["label"]

print(Fore.YELLOW + f"  Test samples: {len(X_test)}")

# ── Predict ───────────────────────────────────────────────────────────────────
X_test_scaled = scaler.transform(X_test)
y_pred        = model.predict(X_test_scaled)
y_proba       = model.predict_proba(X_test_scaled)[:, 1]

# ── Classification report ─────────────────────────────────────────────────────
print("\n" + classification_report(y_test, y_pred,
                                   target_names=["Correct (0)", "Mismatch (1)"]))

# ── Confusion matrix ──────────────────────────────────────────────────────────
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()

print("Confusion Matrix:")
print(f"              Predicted 0   Predicted 1")
print(f"Actual 0:     {tn:>11}   {fp:>11}")
print(f"Actual 1:     {fn:>11}   {tp:>11}")

# ── Metrics with colour thresholds ───────────────────────────────────────────
f1  = f1_score(y_test, y_pred)
acc = accuracy_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_proba)

f1_color  = Fore.GREEN if f1  > 0.80 else Fore.RED
acc_color = Fore.GREEN if acc > 0.85 else Fore.RED
auc_color = Fore.GREEN if auc > 0.85 else Fore.RED

print(f"\n{f1_color}Test F1       : {f1:.4f}")
print(f"{acc_color}Test Accuracy : {acc:.4f}")
print(f"{auc_color}Test AUC-ROC  : {auc:.4f}")

# ── Save results ──────────────────────────────────────────────────────────────
results = {
    "test_f1":       float(f1),
    "test_accuracy": float(acc),
    "test_auc":      float(auc),
    "evaluated_at":  datetime.now().isoformat(),
}

out_path = os.path.join(DATA_DIR, "classifier_eval_results.json")
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=2)

print(Fore.GREEN + f"\n📁 Results saved → data/classifier_eval_results.json")
