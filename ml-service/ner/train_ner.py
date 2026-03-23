import os
import json
import numpy as np
from datasets import Dataset
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
)
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score
from colorama import init, Fore

init(autoreset=True)

# ── SECTION 2: Config ─────────────────────────────────────────────────────────
MODEL_NAME    = "distilbert-base-uncased"
MAX_LENGTH    = 128
BATCH_SIZE    = 16
EPOCHS        = 5
LEARNING_RATE = 2e-5
SAVE_PATH     = os.path.join(os.path.dirname(__file__), "saved_model")
DATA_DIR      = os.path.join(os.path.dirname(__file__), "..", "data")

# ── SECTION 3: Load data ──────────────────────────────────────────────────────
def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

train_records = load_jsonl(os.path.join(DATA_DIR, "ner_train.jsonl"))
val_records   = load_jsonl(os.path.join(DATA_DIR, "ner_val.jsonl"))

with open(os.path.join(DATA_DIR, "ner_label_map.json"), encoding="utf-8") as f:
    label2id = json.load(f)

id2label = {v: k for k, v in label2id.items()}

print(Fore.YELLOW + f"  Loaded {len(train_records)} train / {len(val_records)} val samples")
print(Fore.YELLOW + f"  Labels: {list(label2id.keys())}")

# ── SECTION 4: Tokenize + align labels ───────────────────────────────────────
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def tokenize_and_align_labels(examples):
    tokenized = tokenizer(
        examples["tokens"],
        is_split_into_words=True,
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length",
    )

    all_labels = []
    for i, ner_tags in enumerate(examples["ner_tags"]):
        word_ids       = tokenized.word_ids(batch_index=i)
        prev_word_id   = None
        label_ids      = []

        for word_id in word_ids:
            if word_id is None:
                # Special token ([CLS], [SEP], [PAD])
                label_ids.append(-100)
            elif word_id == prev_word_id:
                # Continuation subword token → ignore
                label_ids.append(-100)
            else:
                label_ids.append(ner_tags[word_id])

            prev_word_id = word_id

        all_labels.append(label_ids)

    tokenized["labels"] = all_labels
    return tokenized


# Convert string labels → integer IDs before creating Dataset
for item in train_records:
    item["ner_tags"] = [label2id[tag] for tag in item["ner_tags"]]
for item in val_records:
    item["ner_tags"] = [label2id[tag] for tag in item["ner_tags"]]

# Convert to HuggingFace Dataset and apply tokenization
train_dataset = Dataset.from_list(train_records)
val_dataset   = Dataset.from_list(val_records)

tokenized_train = train_dataset.map(
    tokenize_and_align_labels,
    batched=True,
    desc="Tokenizing train",
)
tokenized_val = val_dataset.map(
    tokenize_and_align_labels,
    batched=True,
    desc="Tokenizing val",
)

# ── SECTION 5: Model init ─────────────────────────────────────────────────────
model = AutoModelForTokenClassification.from_pretrained(
    MODEL_NAME,
    num_labels=9,
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=True,
)

# ── SECTION 6: compute_metrics ───────────────────────────────────────────────
def compute_metrics(eval_preds):
    logits, labels = eval_preds
    predictions    = np.argmax(logits, axis=-1)

    true_labels = [
        [id2label[l] for l in label_row if l != -100]
        for label_row in labels
    ]
    true_preds = [
        [id2label[p] for p, l in zip(pred_row, label_row) if l != -100]
        for pred_row, label_row in zip(predictions, labels)
    ]

    return {
        "f1":        f1_score(true_labels, true_preds),
        "precision": precision_score(true_labels, true_preds),
        "recall":    recall_score(true_labels, true_preds),
    }

# ── SECTION 7: TrainingArguments ─────────────────────────────────────────────
training_args = TrainingArguments(
    output_dir=SAVE_PATH,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    learning_rate=LEARNING_RATE,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    logging_dir=os.path.join(SAVE_PATH, "logs"),
    logging_steps=50,
    fp16=torch.cuda.is_available(),
    report_to="none",
)

# ── SECTION 8: Trainer + train ───────────────────────────────────────────────
data_collator = DataCollatorForTokenClassification(tokenizer)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val,
    processing_class=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

device = "GPU (CUDA)" if torch.cuda.is_available() else "CPU"
print(Fore.YELLOW + f"\n🚀 Starting NER training on {device}")
print(Fore.YELLOW + f"   Model      : {MODEL_NAME}")
print(Fore.YELLOW + f"   Epochs     : {EPOCHS}")
print(Fore.YELLOW + f"   Batch size : {BATCH_SIZE}")
print(Fore.YELLOW + f"   LR         : {LEARNING_RATE}")
print(Fore.YELLOW + f"   Train size : {len(tokenized_train)}")
print(Fore.YELLOW + f"   Val size   : {len(tokenized_val)}\n")

trainer.train()

trainer.save_model(SAVE_PATH)
tokenizer.save_pretrained(SAVE_PATH)

print(Fore.GREEN + f"✅ NER model trained and saved to ner/saved_model/")
print(Fore.GREEN + f"📁 Model files saved")

# ── SECTION 9: Final metrics summary ─────────────────────────────────────────
log_history = trainer.state.log_history

# Find the last eval metrics entry
final_metrics = {}
for entry in reversed(log_history):
    if "eval_f1" in entry:
        final_metrics = entry
        break

f1        = final_metrics.get("eval_f1",        0.0)
precision = final_metrics.get("eval_precision",  0.0)
recall    = final_metrics.get("eval_recall",     0.0)

print(Fore.YELLOW + "\n📊 Final Training Metrics:")
print(Fore.YELLOW + f"   F1 Score    : {f1:.4f}")
print(Fore.YELLOW + f"   Precision   : {precision:.4f}")
print(Fore.YELLOW + f"   Recall      : {recall:.4f}")
