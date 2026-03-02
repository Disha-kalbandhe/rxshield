import os
import re
import json
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

BASE_DIR  = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "saved_model")
DATA_DIR  = os.path.join(BASE_DIR, "..", "data")

# ── SECTION 1: Lazy model loading ─────────────────────────────────────────────
_model     = None
_tokenizer = None
_id2label  = None
_device    = None


def load_ner_model():
    global _model, _tokenizer, _id2label, _device
    if _model is None:
        _device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        _model     = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)

        with open(os.path.join(DATA_DIR, "ner_label_map.json"), encoding="utf-8") as f:
            label2id = json.load(f)
        _id2label = {v: k for k, v in label2id.items()}

        _model.to(_device)
        _model.eval()
        print("✅ NER model loaded")


# ── SECTION 2: Core extraction function ───────────────────────────────────────
def extract_entities(prescription_text: str) -> dict:
    load_ner_model()

    # Tokenize raw text (same scheme used during training in prepare_ner_data.py)
    tokens = re.findall(r"\w+|[^\w\s]", prescription_text)

    # ── Inference (mirrors predict_ner in evaluate_ner.py) ────────────────────
    tokenized = _tokenizer(
        tokens,
        is_split_into_words=True,
        truncation=True,
        max_length=128,
        return_tensors="pt",
    )
    word_ids  = tokenized.word_ids(batch_index=0)
    tokenized = {k: v.to(_device) for k, v in tokenized.items()}

    with torch.no_grad():
        outputs = _model(**tokenized)

    predictions = np.argmax(outputs.logits[0].cpu().numpy(), axis=-1)

    # Align subword predictions back to original word tokens
    pred_labels  = []
    prev_word_id = None
    for word_id, pred_id in zip(word_ids, predictions):
        if word_id is None:           # [CLS] / [SEP] special tokens
            continue
        if word_id == prev_word_id:   # continuation subword — skip
            continue
        pred_labels.append(_id2label[int(pred_id)])
        prev_word_id = word_id

    # ── Span grouping ─────────────────────────────────────────────────────────
    _label_to_key = {
        "DRUG":     "drugs",
        "DOSE":     "doses",
        "FREQ":     "frequencies",
        "DURATION": "durations",
    }

    entities = {"drugs": [], "doses": [], "frequencies": [], "durations": []}

    current_tokens = []
    current_type   = None

    def _close_span():
        if current_tokens and current_type in _label_to_key:
            entities[_label_to_key[current_type]].append(" ".join(current_tokens))

    for token, label in zip(tokens, pred_labels):
        if label.startswith("B-"):
            _close_span()
            current_tokens = [token]
            current_type   = label[2:]          # "B-DRUG" → "DRUG"
        elif label.startswith("I-") and current_type == label[2:]:
            current_tokens.append(token)        # extend current span
        else:
            _close_span()                       # O or mismatched I-
            current_tokens = []
            current_type   = None

    _close_span()   # flush any trailing open span

    return {
        "drugs":             entities["drugs"],
        "doses":             entities["doses"],
        "frequencies":       entities["frequencies"],
        "durations":         entities["durations"],
        "raw_tokens":        tokens,
        "raw_labels":        pred_labels,
        "prescription_text": prescription_text,
    }


# ── SECTION 3: Test block ──────────────────────────────────────────────────────
if __name__ == "__main__":
    test_texts = [
        "Rx: Metformin 500 mg twice daily for 30 days",
        "Tab Amoxicillin 500mg TID x 7 days, Tab Paracetamol 500mg BD x 5 days",
        "Inj Morphine 10mg IV once, Tab Omeprazole 20mg OD 14 days",
        "Aspirin 75mg once daily, Atorvastatin 20mg at night for 90 days",
        "Metronidazole 400mg three times daily for 5 days, ORS as needed",
    ]

    for text in test_texts:
        result = extract_entities(text)
        print(f"Input: {text}")
        print(f"Drugs    : {result['drugs']}")
        print(f"Doses    : {result['doses']}")
        print(f"Frequency: {result['frequencies']}")
        print(f"Duration : {result['durations']}")
        print("---")
