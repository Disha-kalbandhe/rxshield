import os
import json
import pandas as pd
import jellyfish

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

# ── SECTION 1: Module-level data loading (once on import) ─────────────────────
_lasa_df       = pd.read_csv(os.path.join(DATA_DIR, "lasa_pairs.csv"))
_formulary_df  = pd.read_csv(os.path.join(DATA_DIR, "drug_formulary.csv"))

drug_formulary_list: list = (
    _formulary_df["drug_name"]
    .dropna()
    .str.strip()
    .str.lower()
    .unique()
    .tolist()
)

# Build bidirectional lookup: drug → list of { partner, risk_level, notes }
lasa_lookup: dict = {}

for _, row in _lasa_df.iterrows():
    a     = str(row["drug_a"]).strip().lower()
    b     = str(row["drug_b"]).strip().lower()
    risk  = str(row["risk_level"]).strip()
    notes = str(row["notes"]).strip()

    lasa_lookup.setdefault(a, []).append(
        {"partner": row["drug_b"].strip(), "risk_level": risk, "notes": notes}
    )
    lasa_lookup.setdefault(b, []).append(
        {"partner": row["drug_a"].strip(), "risk_level": risk, "notes": notes}
    )


# ── SECTION 2: Exact LASA pair lookup ─────────────────────────────────────────
def check_known_lasa_pairs(drug_name: str) -> list:
    """Return known LASA partners from the curated pair list."""
    return lasa_lookup.get(drug_name.strip().lower(), [])


# ── SECTION 3: Phonetic similarity ────────────────────────────────────────────
def get_phonetic_matches(drug_name: str, threshold: float = 0.75) -> list:
    """
    Compare drug_name against every drug in the formulary using
    Levenshtein similarity, Jaro-Winkler similarity, and Soundex.
    Returns matches whose combined score >= threshold, sorted desc.
    """
    drug_lower   = drug_name.strip().lower()
    drug_soundex = jellyfish.soundex(drug_lower)

    matches = []

    for known_drug in drug_formulary_list:
        if known_drug == drug_lower:
            continue

        known_soundex = jellyfish.soundex(known_drug)

        lev_distance  = jellyfish.levenshtein_distance(drug_lower, known_drug)
        max_len       = max(len(drug_lower), len(known_drug))
        lev_similarity = 1 - (lev_distance / max_len)

        jaro_sim      = jellyfish.jaro_winkler_similarity(drug_lower, known_drug)
        soundex_match = drug_soundex == known_soundex

        combined_score = (
            lev_similarity * 0.4
            + jaro_sim     * 0.4
            + (0.2 if soundex_match else 0)
        )

        if combined_score >= threshold:
            matches.append({
                "similar_drug":            known_drug,
                "levenshtein_similarity":  round(lev_similarity, 3),
                "jaro_winkler":            round(jaro_sim, 3),
                "soundex_match":           soundex_match,
                "combined_score":          round(combined_score, 3),
            })

    return sorted(matches, key=lambda x: x["combined_score"], reverse=True)


# ── SECTION 4: Main LASA check function ───────────────────────────────────────
def check_lasa_confusion(drug_name: str) -> dict:
    """
    Full LASA risk assessment combining curated pair lookup with
    phonetic/orthographic similarity scoring.
    """
    known_pairs      = check_known_lasa_pairs(drug_name)
    phonetic_matches = get_phonetic_matches(drug_name, threshold=0.72)

    # Remove phonetic matches already covered by curated pairs
    known_partners = {p["partner"].lower() for p in known_pairs}
    new_phonetic   = [
        m for m in phonetic_matches
        if m["similar_drug"] not in known_partners
    ]

    has_lasa_risk = len(known_pairs) > 0 or len(new_phonetic) > 0

    # Determine highest overall risk level
    risk_order = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
    risk_level = "NONE"

    if known_pairs:
        highest    = max(known_pairs,
                         key=lambda x: risk_order.get(x["risk_level"], 0))
        risk_level = highest["risk_level"]
    elif new_phonetic and new_phonetic[0]["combined_score"] > 0.85:
        risk_level = "MEDIUM"
    elif new_phonetic:
        risk_level = "LOW"

    if has_lasa_risk:
        partners_list = [p["partner"] for p in known_pairs]
        recommendation = (
            f"⚠️ LASA Alert: '{drug_name}' may be confused with "
            f"{partners_list}. Verify drug name."
        )
    else:
        recommendation = f"✅ No significant LASA risk detected for '{drug_name}'"

    return {
        "drug_name":              drug_name,
        "has_lasa_risk":          has_lasa_risk,
        "risk_level":             risk_level,
        "known_lasa_pairs":       known_pairs,
        "phonetic_similar_drugs": new_phonetic[:3],
        "total_similar_found":    len(known_pairs) + len(new_phonetic),
        "recommendation":         recommendation,
    }


# ── SECTION 5: Quick smoke test ───────────────────────────────────────────────
if __name__ == "__main__":
    for drug in ["Metformin", "Morphine", "Digoxin"]:
        r = check_lasa_confusion(drug)
        print(f"{drug:20} risk={r['risk_level']:8} "
              f"known={[p['partner'] for p in r['known_lasa_pairs']]} "
              f"phonetic={[m['similar_drug'] for m in r['phonetic_similar_drugs']]}")
