import sys
import os

# Ensure lasa_detector can be found when run from any working directory
sys.path.insert(0, os.path.dirname(__file__))

from lasa_detector import check_lasa_confusion

test_drugs = [
    "Metformin",      # Known LASA: Metronidazole
    "Tramadol",       # Known LASA: Toradol (CRITICAL)
    "Morphine",       # Known LASA: Hydromorphone (CRITICAL)
    "Aspirin",        # Minor phonetic matches
    "Amoxicillin",    # Known LASA: Amoxapine
    "Paracetamol",    # Should show phonetic matches
    "Digoxin",        # Known LASA: Doxepin (CRITICAL)
    "Ciprofloxacin",  # Unique name, low matches expected
]

for drug in test_drugs:
    result = check_lasa_confusion(drug)
    print(f"\n{'='*50}")
    print(f"Drug: {result['drug_name']}")
    print(f"LASA Risk: {result['risk_level']}")
    print(f"Known pairs: {[p['partner'] for p in result['known_lasa_pairs']]}")
    print(f"Phonetic: {[m['similar_drug'] for m in result['phonetic_similar_drugs']]}")
    print(f"→ {result['recommendation']}")
