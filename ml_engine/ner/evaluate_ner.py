import os
import json
import random
import numpy as np
import torch
from datetime import datetime
from tqdm import tqdm
from colorama import init, Fore
from transformers import AutoTokenizer, AutoModelForTokenClassification
from seqeval.metrics import (
    classification_report, f1_score, precision_score, recall_score, accuracy_score,
)

init(autoreset=True)

BASE_DIR  = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "saved_model")
DATA_DIR  = os.path.join(BASE_DIR, "..", "data")

# ── SECTION 1: Load model and tokenizer ───────────────────────────────────────
print(Fore.YELLOW + "  Loading model from saved_model/...")

with open(os.path.join(DATA_DIR, "ner_label_map.json"), encoding="utf-8") as f:
    label2id = json.load(f)

id2label = {v: k for k, v in label2id.items()}

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model     = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model  = model.to(device)
model.eval()

print(Fore.YELLOW + f"  Model loaded  | Labels: {len(id2label)} | Device: {device}")

# ── SECTION 2: Load test data ─────────────────────────────────────────────────
test_path = os.path.join(DATA_DIR, "ner_test.jsonl")
with open(test_path, encoding="utf-8") as f:
    test_records = [json.loads(line) for line in f if line.strip()]

print(Fore.YELLOW + f"  Loaded {len(test_records)} test samples\n")

# ── SECTION 3: Predict function ───────────────────────────────────────────────
def predict_ner(tokens, model, tokenizer, id2label, max_length=128):
    tokenized = tokenizer(
        tokens,
        is_split_into_words=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    word_ids  = tokenized.word_ids(batch_index=0)
    tokenized = {k: v.to(device) for k, v in tokenized.items()}

    model.eval()
    with torch.no_grad():
        outputs = model(**tokenized)

    predictions = np.argmax(outputs.logits[0].cpu().numpy(), axis=-1)

    pred_labels   = []
    prev_word_id  = None
    for word_id, pred_id in zip(word_ids, predictions):
        if word_id is None:               # [CLS] / [SEP] / [PAD]
            continue
        if word_id == prev_word_id:       # continuation subword
            continue
        pred_labels.append(id2label[int(pred_id)])
        prev_word_id = word_id

    return pred_labels

# ── SECTION 4: Run evaluation on full test set ────────────────────────────────
all_true_labels: list[list[str]] = []
all_pred_labels: list[list[str]] = []

for record in tqdm(test_records, desc="Evaluating", unit="sample"):
    tokens    = record["tokens"]
    true_tags = record["ner_tags"]

    pred_tags = predict_ner(tokens, model, tokenizer, id2label)

    # Sequences may differ if text was truncated at MAX_LENGTH
    min_len   = min(len(true_tags), len(pred_tags))
    all_true_labels.append(true_tags[:min_len])
    all_pred_labels.append(pred_tags[:min_len])

# ── SECTION 5: Compute and display metrics ────────────────────────────────────
report = classification_report(all_true_labels, all_pred_labels)
f1     = f1_score(all_true_labels, all_pred_labels)
prec   = precision_score(all_true_labels, all_pred_labels)
rec    = recall_score(all_true_labels, all_pred_labels)

# Per-entity F1 (seqeval groups B-/I- by entity type)
try:
    report_dict = classification_report(
        all_true_labels, all_pred_labels, output_dict=True
    )
    per_entity_f1 = {
        ent: report_dict.get(ent, {}).get("f1-score", 0.0)
        for ent in ["DRUG", "DOSE", "FREQ", "DURATION"]
    }
except TypeError:
    # Older seqeval without output_dict support
    per_entity_f1 = {ent: 0.0 for ent in ["DRUG", "DOSE", "FREQ", "DURATION"]}

print("\n" + report)
print(Fore.CYAN  + "=" * 50)
print(Fore.CYAN  + "📊 RxShield NER Model — Test Evaluation")
print(Fore.CYAN  + "=" * 50)
print(Fore.GREEN + f"Overall F1       : {f1:.4f}")
print(Fore.GREEN + f"Overall Precision: {prec:.4f}")
print(Fore.GREEN + f"Overall Recall   : {rec:.4f}")
print(Fore.YELLOW + f"\n  B-DRUG / I-DRUG    F1: {per_entity_f1['DRUG']:.4f}")
print(Fore.YELLOW + f"  B-DOSE / I-DOSE    F1: {per_entity_f1['DOSE']:.4f}")
print(Fore.YELLOW + f"  B-FREQ / I-FREQ    F1: {per_entity_f1['FREQ']:.4f}")
print(Fore.YELLOW + f"  B-DURATION         F1: {per_entity_f1['DURATION']:.4f}")

# ── SECTION 6: Error analysis on 10 examples ─────────────────────────────────
error_indices = [
    i for i in range(len(test_records))
    if all_true_labels[i] != all_pred_labels[i]
]

random.seed(42)
sample_indices = random.sample(error_indices, min(10, len(error_indices)))

print(Fore.CYAN + "\n🔍 Error Analysis — 10 Sample Mismatches")
print(Fore.CYAN + "=" * 50)

for n, idx in enumerate(sample_indices, 1):
    tokens    = test_records[idx]["tokens"]
    true_tags = all_true_labels[idx]
    pred_tags = all_pred_labels[idx]

    print(Fore.YELLOW + f"\nSample {n}  (record {idx}):")
    print(f"  {'Token':<22} {'True Label':<14} Predicted")
    print(f"  {'-'*22} {'-'*14} {'-'*14}")

    for tok, tru, prd in zip(tokens, true_tags, pred_tags):
        mismatch = tru != prd
        color    = Fore.RED if mismatch else ""
        marker   = "✗" if mismatch else " "
        print(color + f"  {marker} {tok:<21} {tru:<14} {prd}")

# ── SECTION 7: Save results ───────────────────────────────────────────────────
results = {
    "f1":           float(f1),
    "precision":    float(prec),
    "recall":       float(rec),
    "per_label_f1": {k: float(v) for k, v in per_entity_f1.items()},
    "test_samples": len(test_records),
    "evaluated_at": datetime.now().isoformat(),
}

out_path = os.path.join(DATA_DIR, "ner_eval_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(Fore.GREEN + "\n📁 Results saved to data/ner_eval_results.json")
