import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from colorama import init, Fore
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, f1_score, accuracy_score, roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

init(autoreset=True)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SAVE_DIR = os.path.join(BASE_DIR, "saved_model")
os.makedirs(SAVE_DIR, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
print(Fore.YELLOW + "  Loading train / val data...")

with open(os.path.join(DATA_DIR, "classifier_feature_columns.json"), encoding="utf-8") as f:
    feature_columns = json.load(f)

train_df = pd.read_csv(os.path.join(DATA_DIR, "classifier_train.csv"))
val_df   = pd.read_csv(os.path.join(DATA_DIR, "classifier_val.csv"))

X_train = train_df[feature_columns]
y_train = train_df["label"]
X_val   = val_df[feature_columns]
y_val   = val_df["label"]

print(Fore.YELLOW + f"  Train samples: {len(X_train)} | Val samples: {len(X_val)}")

# ── Scale features ────────────────────────────────────────────────────────────
scaler          = StandardScaler()
X_train_scaled  = scaler.fit_transform(X_train)
X_val_scaled    = scaler.transform(X_val)

joblib.dump(scaler, os.path.join(SAVE_DIR, "classifier_scaler.joblib"))
print(Fore.YELLOW + "  Scaler saved.")

# ── Train RandomForest ────────────────────────────────────────────────────────
print(Fore.YELLOW + "  Training RandomForestClassifier (n_estimators=200)...")

rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)
rf.fit(X_train_scaled, y_train)

# ── Evaluate on validation set ────────────────────────────────────────────────
y_pred  = rf.predict(X_val_scaled)
y_proba = rf.predict_proba(X_val_scaled)[:, 1]

f1  = f1_score(y_val, y_pred)
acc = accuracy_score(y_val, y_pred)
auc = roc_auc_score(y_val, y_proba)

print("\n" + classification_report(y_val, y_pred,
                                   target_names=["Correct (0)", "Mismatch (1)"]))

# ── Feature importance plot ───────────────────────────────────────────────────
importances = pd.Series(rf.feature_importances_, index=feature_columns)
top10       = importances.nlargest(10).sort_values()

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x=top10.values, y=top10.index, ax=ax, palette="viridis")
ax.set_title("RxShield - Drug-Indication Mismatch: Feature Importance")
ax.set_xlabel("Importance")
ax.set_ylabel("Feature")
plt.tight_layout()
plot_path = os.path.join(SAVE_DIR, "feature_importance.png")
fig.savefig(plot_path, dpi=150)
plt.close(fig)
print(Fore.YELLOW + f"  Feature importance plot saved → {plot_path}")

# ── Save model ────────────────────────────────────────────────────────────────
model_path = os.path.join(SAVE_DIR, "classifier_model.joblib")
joblib.dump(rf, model_path, compress=3)

# ── Save training metadata ────────────────────────────────────────────────────
metadata = {
    "model_type":       "RandomForestClassifier",
    "n_estimators":     200,
    "val_f1":           float(f1),
    "val_accuracy":     float(acc),
    "val_auc":          float(auc),
    "feature_columns":  feature_columns,
    "trained_at":       datetime.now().isoformat(),
}
with open(os.path.join(SAVE_DIR, "training_metadata.json"), "w", encoding="utf-8") as fh:
    json.dump(metadata, fh, indent=2)

# ── Print summary ─────────────────────────────────────────────────────────────
print(Fore.GREEN + "\n✅ Classifier model trained!")
print(Fore.GREEN + f"📊 Validation F1      : {f1:.4f}")
print(Fore.GREEN + f"📊 Validation Accuracy: {acc:.4f}")
print(Fore.GREEN + f"📊 Validation AUC-ROC : {auc:.4f}")
print(Fore.GREEN + "📁 Model saved: classifier/saved_model/")
