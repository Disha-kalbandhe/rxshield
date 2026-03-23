import json
import re
import random
import os
from collections import Counter
from tqdm import tqdm
from colorama import init, Fore

# ── Init ───────────────────────────────────────────────────────────────────────
init(autoreset=True)
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

LABEL_MAP = {
    "O":          0,
    "B-DRUG":     1,
    "I-DRUG":     2,
    "B-DOSE":     3,
    "I-DOSE":     4,
    "B-FREQ":     5,
    "I-FREQ":     6,
    "B-DURATION": 7,
    "I-DURATION": 8,
}

# Priority order for greedy matching (highest priority first)
ENTITY_PRIORITY = ["DRUG", "DOSE", "FREQ", "DURATION"]


# ── Helpers ────────────────────────────────────────────────────────────────────
def tokenize(text):
    """Whitespace + punctuation tokenizer matching the tagging logic."""
    return re.findall(r"\w+|[^\w\s]", str(text))


def build_entity_sets(prescription):
    """
    Extract BIO entity spans from a prescription's prescribed_drugs list.
    Returns dict: label -> set of token-tuples (lowercased).
    """
    entities = {label: set() for label in ENTITY_PRIORITY}

    for drug_obj in prescription.get("prescribed_drugs", []):
        # DRUG
        name = drug_obj.get("drug_name", "")
        if name:
            toks = tuple(t.lower() for t in tokenize(name))
            if toks:
                entities["DRUG"].add(toks)

        # DOSE — "500 mg", "10 units", etc.
        dose_mg   = drug_obj.get("dose_mg")
        dose_unit = drug_obj.get("dose_unit", "mg")
        if dose_mg is not None:
            dose_str = f"{dose_mg} {dose_unit}"
            toks = tuple(t.lower() for t in tokenize(dose_str))
            if toks:
                entities["DOSE"].add(toks)

        # FREQ
        freq = drug_obj.get("frequency", "")
        if freq:
            toks = tuple(t.lower() for t in tokenize(freq))
            if toks:
                entities["FREQ"].add(toks)

        # DURATION — "7 days"
        dur = drug_obj.get("duration_days")
        if dur is not None:
            dur_str = f"{dur} days"
            toks = tuple(t.lower() for t in tokenize(dur_str))
            if toks:
                entities["DURATION"].add(toks)

    return entities


def build_first_token_index(entity_sets):
    """
    Build a lookup: (label, first_token_lower) → list of token-tuples
    sorted by length descending (longest-match-first).
    Priority order is preserved by checking labels in ENTITY_PRIORITY order.
    """
    index = {}
    for label in ENTITY_PRIORITY:
        for tup in entity_sets[label]:
            key = (label, tup[0])
            index.setdefault(key, []).append(tup)
    for key in index:
        index[key].sort(key=lambda x: -len(x))
    return index


def bio_tag(tokens, index):
    """
    Greedily BIO-tag tokens using the entity index.
    Priority: DRUG > DOSE > FREQ > DURATION (enforced by label order checks).
    """
    n          = len(tokens)
    tags       = ["O"] * n
    toks_lower = [t.lower() for t in tokens]

    i = 0
    while i < n:
        matched = False

        for label in ENTITY_PRIORITY:
            key = (label, toks_lower[i])
            candidates = index.get(key, [])

            for entity_toks in candidates:           # already sorted longest-first
                span = len(entity_toks)
                if i + span > n:
                    continue
                if toks_lower[i:i + span] == list(entity_toks):
                    tags[i] = f"B-{label}"
                    for j in range(1, span):
                        tags[i + j] = f"I-{label}"
                    i      += span
                    matched = True
                    break

            if matched:
                break

        if not matched:
            i += 1

    return tags


def write_jsonl(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ── Load data ──────────────────────────────────────────────────────────────────
aug_path = os.path.join(DATA_DIR, "augmented_prescriptions.json")
with open(aug_path, encoding="utf-8") as f:
    all_prescriptions = json.load(f)

# Only correct prescriptions for NER training
correct = [rx for rx in all_prescriptions if rx.get("is_correct") is True]
print(Fore.YELLOW + f"  Using {len(correct)} correct prescriptions for NER")

# ── STEP 1–3: Tokenize + tag ───────────────────────────────────────────────────
ner_samples = []

for rx in tqdm(correct, desc="Tokenizing & tagging", unit="rx"):
    text = rx.get("prescription_text", "")
    if not text or not text.strip():
        continue

    tokens       = tokenize(text)
    entity_sets  = build_entity_sets(rx)
    index        = build_first_token_index(entity_sets)
    tags         = bio_tag(tokens, index)

    ner_samples.append({"tokens": tokens, "ner_tags": tags})

# ── STEP 4: Split ──────────────────────────────────────────────────────────────
random.seed(42)
random.shuffle(ner_samples)

n       = len(ner_samples)
n_train = int(n * 0.70)
n_val   = int(n * 0.15)

train_data = ner_samples[:n_train]
val_data   = ner_samples[n_train:n_train + n_val]
test_data  = ner_samples[n_train + n_val:]

# ── STEP 5: Save ───────────────────────────────────────────────────────────────
train_path     = os.path.join(DATA_DIR, "ner_train.jsonl")
val_path       = os.path.join(DATA_DIR, "ner_val.jsonl")
test_path      = os.path.join(DATA_DIR, "ner_test.jsonl")
label_map_path = os.path.join(DATA_DIR, "ner_label_map.json")

write_jsonl(train_data, train_path)
write_jsonl(val_data,   val_path)
write_jsonl(test_data,  test_path)

with open(label_map_path, "w", encoding="utf-8") as f:
    json.dump(LABEL_MAP, f, indent=2)

# ── STEP 6: Stats ──────────────────────────────────────────────────────────────
all_tags   = [tag for sample in ner_samples for tag in sample["ner_tags"]]
total_toks = len(all_tags)
tag_counts = Counter(all_tags)

print(Fore.GREEN  + "✅ NER dataset prepared")
print(Fore.YELLOW + f"📊 Train: {len(train_data)} samples | "
                    f"Val: {len(val_data)} | Test: {len(test_data)}")
print(Fore.YELLOW + "🏷️  Label distribution:")
for label in LABEL_MAP:
    cnt = tag_counts.get(label, 0)
    pct = cnt / total_toks * 100 if total_toks else 0
    print(Fore.YELLOW + f"       {label:<14} {cnt:>8} tokens  ({pct:5.2f}%)")
print(Fore.GREEN + "📁 Saved to ml-service/data/")
