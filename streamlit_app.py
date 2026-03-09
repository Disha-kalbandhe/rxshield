import sys, os, json, re, io, base64
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_engine'))

import streamlit as st
from PIL import Image

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RxShield — Prescription Safety AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Dark theme base */
  .stApp { background-color: #0f1117; }
  
  /* Header */
  .rx-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #2563eb 100%);
    padding: 2rem 2.5rem; border-radius: 16px;
    margin-bottom: 1.5rem; text-align: center;
  }
  .rx-header h1 { color: white; font-size: 2.2rem; margin: 0; font-weight: 800; }
  .rx-header p  { color: #93c5fd; margin: 0.4rem 0 0; font-size: 1rem; }

  /* Risk badges */
  .badge-safe     { background:#064e3b; color:#6ee7b7; border:1px solid #065f46;
                    padding:6px 16px; border-radius:999px; font-weight:700; }
  .badge-low      { background:#1e3a5f; color:#93c5fd; border:1px solid #1e40af;
                    padding:6px 16px; border-radius:999px; font-weight:700; }
  .badge-medium   { background:#451a03; color:#fbbf24; border:1px solid #92400e;
                    padding:6px 16px; border-radius:999px; font-weight:700; }
  .badge-high     { background:#431407; color:#fb923c; border:1px solid #9a3412;
                    padding:6px 16px; border-radius:999px; font-weight:700; }
  .badge-critical { background:#450a0a; color:#f87171; border:1px solid #991b1b;
                    padding:6px 16px; border-radius:999px; font-weight:700; }

  /* Error cards */
  .card-critical { background:#1c0a0a; border:1px solid #991b1b;
                   border-left:4px solid #ef4444; border-radius:12px; padding:1rem; margin:0.5rem 0; }
  .card-high     { background:#1c1208; border:1px solid #9a3412;
                   border-left:4px solid #f97316; border-radius:12px; padding:1rem; margin:0.5rem 0; }
  .card-medium   { background:#1c1a08; border:1px solid #92400e;
                   border-left:4px solid #eab308; border-radius:12px; padding:1rem; margin:0.5rem 0; }
  .card-drug     { background:#111827; border:1px solid #374151;
                   border-radius:10px; padding:0.75rem 1rem; margin:0.3rem 0; }
  
  /* Stats row */
  .stat-box { background:#111827; border:1px solid #1f2937;
              border-radius:12px; padding:1rem; text-align:center; }
  .stat-num { font-size:2rem; font-weight:800; color:#60a5fa; }
  .stat-lbl { font-size:0.75rem; color:#6b7280; margin-top:2px; }

  /* Streamlit overrides */
  .stTextArea textarea { background:#111827 !important; color:white !important;
                         border:1px solid #374151 !important; border-radius:12px !important; }
  .stSelectbox > div   { background:#111827 !important; }
  div[data-testid="stMetricValue"] { color: #60a5fa; }
  
  /* Section headers */
  .section-title { color:#93c5fd; font-size:0.8rem; font-weight:700;
                   text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rx-header">
  <h1>🛡️ RxShield</h1>
  <p>AI-Powered Prescription Safety System &nbsp;•&nbsp; 
     Detect DDI • Allergy • Dosage • LASA Errors</p>
</div>
""", unsafe_allow_html=True)

# ── Load ML modules ───────────────────────────────────────────────────────────
@st.cache_resource
def load_modules():
    """Load rules engine. Cached — loads only once per session."""
    try:
        from rules.rules_engine import run_all_checks
        from ocr.ocr_pipeline import (ocr_from_base64,
                                       resolve_drugs_from_text,
                                       clean_prescription_text)
        return run_all_checks, ocr_from_base64, resolve_drugs_from_text, clean_prescription_text, True
    except Exception as e:
        return None, None, None, None, False

run_all_checks, ocr_from_base64, resolve_drugs_from_text, clean_prescription_text, modules_ok = load_modules()

if not modules_ok:
    st.error("⚠️ Could not load ML modules. Check that ml_engine/ is in the project root.")
    st.stop()

# ── Sidebar — Patient Information ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👤 Patient Information")
    st.caption("Fill patient details for accurate analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=1, max_value=120, value=45, step=1)
    with col2:
        weight = st.number_input("Weight (kg)", min_value=10, max_value=200, value=70, step=1)
    
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    
    st.markdown("**Allergies** *(one per line)*")
    allergies_raw = st.text_area(
        "allergies", label_visibility="collapsed",
        placeholder="Penicillin\nSulfa\nAspirin",
        height=90
    )
    
    st.markdown("**Diagnosis** *(one per line)*")
    diagnosis_raw = st.text_area(
        "diagnosis", label_visibility="collapsed",
        placeholder="Type 2 Diabetes\nHypertension\nAtrial Fibrillation",
        height=90
    )
    
    allergies = [a.strip() for a in allergies_raw.split('\n') if a.strip()]
    diagnoses = [d.strip() for d in diagnosis_raw.split('\n') if d.strip()]
    
    st.markdown("---")
    st.markdown("**Language**")
    language = st.selectbox(
        "lang", label_visibility="collapsed",
        options=["english", "hindi", "marathi", "hindi+marathi"],
        format_func=lambda x: {
            "english": "🇬🇧 English",
            "hindi":   "🇮🇳 Hindi (हिंदी)",
            "marathi": "🇮🇳 Marathi (मराठी)",
            "hindi+marathi": "🇮🇳 Hindi + Marathi"
        }[x]
    )
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#4b5563;font-size:0.75rem'>"
        "RxShield v1.0 • Hackathon Demo<br>"
        "Built with ❤️ using Gemini AI"
        "</div>", unsafe_allow_html=True
    )

# ── Patient data dict ─────────────────────────────────────────────────────────
patient_data = {
    "age": age,
    "gender": gender,
    "weight_kg": weight,
    "allergies": allergies,
    "diagnosis": diagnoses,
    "current_medications": [],
    "comorbidities": []
}

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📝 Text Input", "📷 Image Upload (OCR)"])

drug_list = []
raw_text_for_display = ""

# ══════════════════════════════════════════════════════
# TAB 1 — TEXT INPUT
# ══════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.markdown('<p class="section-title">📋 Prescription Text</p>',
                    unsafe_allow_html=True)
        
        # Quick-fill demo buttons
        st.caption("🧪 Load a test case:")
        demo_cols = st.columns(3)
        
        DEMOS = {
            "✅ Safe":
                "1. Metformin 500mg BD\n2. Amlodipine 5mg OD\n3. Pantoprazole 40mg AC",
            "⚡ DDI":
                "1. Warfarin 5mg OD\n2. Aspirin 500mg TID\n3. Digoxin 0.25mg OD",
            "💊 Overdose":
                "1. Metformin 5000mg BD\n2. Atorvastatin 40mg HS\n3. Lisinopril 10mg OD",
        }
        
        if "demo_text" not in st.session_state:
            st.session_state.demo_text = ""
        
        for i, (label, text) in enumerate(DEMOS.items()):
            with demo_cols[i]:
                if st.button(label, use_container_width=True, key=f"demo_{i}"):
                    st.session_state.demo_text = text
        
        prescription_text = st.text_area(
            "Enter prescription text",
            value=st.session_state.demo_text,
            height=220,
            placeholder="1. Metformin 500mg - 1 tab BD\n2. Amlodipine 5mg - 1 tab OD\n...",
            label_visibility="collapsed"
        )
        
        analyze_btn = st.button("🔍 Analyze Prescription",
                                 type="primary",
                                 use_container_width=True,
                                 key="analyze_text")
    
    with col_right:
        if analyze_btn and prescription_text.strip():
            with st.spinner("🤖 Analyzing prescription..."):
                # Extract drugs from text using Gemini
                resolved = resolve_drugs_from_text(prescription_text)
                if resolved:
                    drug_list = [r["correct_name"] for r in resolved]
                    extracted_drugs_raw = [
                        {"drug_name": r["correct_name"], "dose": r.get("dose")}
                        for r in resolved
                    ]
                else:
                    # Fallback regex extraction
                    pattern = re.compile(
                        r'\b(Metformin|Aspirin|Warfarin|Amoxicillin|Atorvastatin|'
                        r'Amlodipine|Lisinopril|Metoprolol|Betaloc|Atenolol|'
                        r'Digoxin|Furosemide|Tramadol|Codeine|Ibuprofen|'
                        r'Diclofenac|Paracetamol|Omeprazole|Pantoprazole|'
                        r'Ciprofloxacin|Azithromycin|Clarithromycin|'
                        r'Simvastatin|Rosuvastatin|Cimetidine|Ranitidine|'
                        r'Spironolactone|Telmisartan|Glimepiride|Cetirizine)\b',
                        re.IGNORECASE
                    )
                    drug_list = list(dict.fromkeys(
                        m.group(0) for m in pattern.finditer(prescription_text)
                    ))
                    extracted_drugs_raw = [{"drug_name": d, "dose": None} for d in drug_list]
                
                raw_text_for_display = prescription_text
                
                if drug_list:
                    result = run_all_checks(
                        drug_names=drug_list,
                        patient_data=patient_data,
                        extracted_drugs=extracted_drugs_raw
                    )
                    st.session_state.result = result
                    st.session_state.drug_list = drug_list
                    st.session_state.resolved = resolved if resolved else []
                else:
                    st.warning("⚠️ No drug names detected. Try the demo cases.")
        
        elif analyze_btn:
            st.warning("Please enter prescription text first.")

# ══════════════════════════════════════════════════════
# TAB 2 — IMAGE UPLOAD
# ══════════════════════════════════════════════════════
with tab2:
    col_left2, col_right2 = st.columns([1, 1], gap="large")
    
    with col_left2:
        st.markdown('<p class="section-title">📷 Upload Prescription Image</p>',
                    unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose prescription image",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.image(img, caption="Uploaded Prescription", use_column_width=True)
        
        ocr_btn = st.button("🔍 Extract & Analyze",
                             type="primary",
                             use_container_width=True,
                             key="analyze_img",
                             disabled=not uploaded_file)
    
    with col_right2:
        if ocr_btn and uploaded_file:
            # Step 1: OCR
            with st.spinner("🤖 Extracting text with Gemini Vision..."):
                try:
                    img_bytes = uploaded_file.getvalue()
                    b64 = base64.b64encode(img_bytes).decode()
                    ocr_result = ocr_from_base64(b64, language=language)
                    
                    raw_text = ocr_result.get("cleanedText") or ocr_result.get("text", "")
                    structured = ocr_result.get("structured", {})
                    drugs_from_ocr = structured.get("drugs", [])
                    
                    st.success(f"✅ OCR complete — {ocr_result.get('charCount',0)} chars extracted")
                    
                    with st.expander("📄 View Extracted Text", expanded=False):
                        st.text(raw_text[:1500] + ("..." if len(raw_text)>1500 else ""))
                
                except Exception as e:
                    st.error(f"OCR failed: {e}")
                    st.stop()
            
            # Step 2: Resolve drugs
            with st.spinner("💊 Identifying drug names..."):
                if drugs_from_ocr:
                    drug_list = [d["name"] for d in drugs_from_ocr if d.get("name")]
                    extracted_drugs_raw = [
                        {"drug_name": d["name"], "dose": d.get("dose")}
                        for d in drugs_from_ocr
                    ]
                    resolved_drugs = drugs_from_ocr
                else:
                    resolved_raw = resolve_drugs_from_text(raw_text)
                    drug_list = [r["correct_name"] for r in resolved_raw]
                    extracted_drugs_raw = [
                        {"drug_name": r["correct_name"], "dose": r.get("dose")}
                        for r in resolved_raw
                    ]
                    resolved_drugs = resolved_raw
            
            # Step 3: Analyze
            if drug_list:
                with st.spinner("🔬 Running safety analysis..."):
                    result = run_all_checks(
                        drug_names=drug_list,
                        patient_data=patient_data,
                        extracted_drugs=extracted_drugs_raw
                    )
                    st.session_state.result = result
                    st.session_state.drug_list = drug_list
                    st.session_state.resolved = resolved_drugs
            else:
                st.warning("⚠️ No drug names detected. Ensure image contains a prescription.")


# ══════════════════════════════════════════════════════
# RESULTS PANEL (shared for both tabs)
# ══════════════════════════════════════════════════════
if "result" in st.session_state:
    result   = st.session_state.result
    drugs    = st.session_state.get("drug_list", [])
    resolved = st.session_state.get("resolved", [])
    errors   = result.get("errors", [])
    
    st.markdown("---")
    st.markdown("## 📊 Safety Analysis Report")
    
    # ── Risk level calculation ────────────────────────────────────────────
    sev_weights = {"CRITICAL":1.0,"HIGH":0.7,"MEDIUM":0.4,"LOW":0.2}
    risk_score  = 0.0
    if errors:
        scores = [sev_weights.get(e["severity"],0.1) for e in errors]
        risk_score = min(1.0, max(scores)*0.6 + (len(errors)-1)*0.1)
    
    risk_level = (
        "CRITICAL" if risk_score > 0.75 else
        "HIGH"     if risk_score > 0.5  else
        "MEDIUM"   if risk_score > 0.25 else
        "LOW"      if risk_score > 0    else "SAFE"
    )
    
    # ── Stats row ─────────────────────────────────────────────────────────
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.metric("🎯 Risk Level", risk_level,
                  delta="Safe" if risk_level=="SAFE" else "Review needed",
                  delta_color="normal" if risk_level=="SAFE" else "inverse")
    with s2:
        st.metric("💊 Drugs Found", len(drugs))
    with s3:
        st.metric("⚡ DDI Alerts",  result.get("ddi_count",0))
    with s4:
        st.metric("🚨 Allergies",   result.get("allergy_count",0))
    with s5:
        st.metric("📏 Dosage Issues", result.get("dosage_count",0))
    
    # ── Risk badge ────────────────────────────────────────────────────────
    badge_map = {
        "SAFE":     ("✅ SAFE — No Issues Detected",    "badge-safe"),
        "LOW":      ("🔵 LOW RISK",                    "badge-low"),
        "MEDIUM":   ("⚠️ MEDIUM RISK — Review Required","badge-medium"),
        "HIGH":     ("🔴 HIGH RISK — Action Required",  "badge-high"),
        "CRITICAL": ("🚨 CRITICAL RISK — Do Not Dispense","badge-critical"),
    }
    label, cls = badge_map[risk_level]
    st.markdown(
        f'<div style="margin:1rem 0;font-size:1.1rem">'
        f'<span class="{cls}">{label}</span></div>',
        unsafe_allow_html=True
    )
    
    # ── Extracted drugs ───────────────────────────────────────────────────
    if drugs:
        st.markdown("### 💊 Extracted Drugs")
        drug_cols = st.columns(min(len(drugs), 4))
        for i, drug in enumerate(drugs):
            # Find dose/freq from resolved list
            info = next((r for r in resolved
                         if r.get("correct_name","").lower() == drug.lower()
                         or r.get("name","").lower() == drug.lower()), {})
            dose = info.get("dose","—") or "—"
            freq = info.get("frequency","—") or "—"
            ocr_name = info.get("ocr_name","")
            
            with drug_cols[i % 4]:
                corrected = (ocr_name and
                             ocr_name.lower() != drug.lower())
                correction_badge = (
                    f'<span style="font-size:0.65rem;background:#451a03;'
                    f'color:#fbbf24;padding:1px 6px;border-radius:999px;'
                    f'margin-left:4px">✏️ corrected</span>'
                    if corrected else ""
                )
                st.markdown(
                    f'<div class="card-drug">'
                    f'<div style="color:white;font-weight:600">💊 {drug}</div>'
                    f'{correction_badge}'
                    + (f'<div style="color:#6b7280;font-size:0.7rem;margin-top:2px">'
                       f'OCR: "{ocr_name}"</div>' if corrected else '')
                    + f'<div style="margin-top:4px">'
                      f'<span style="background:#1e3a5f;color:#93c5fd;'
                      f'font-size:0.72rem;padding:2px 8px;border-radius:999px;'
                      f'margin-right:4px">{dose}</span>'
                      f'<span style="background:#2e1065;color:#c4b5fd;'
                      f'font-size:0.72rem;padding:2px 8px;border-radius:999px">'
                      f'{freq}</span>'
                      f'</div></div>',
                    unsafe_allow_html=True
                )
    
    # ── Error cards ───────────────────────────────────────────────────────
    if errors:
        st.markdown("### 🚨 Issues Detected")
        
        TYPE_ICONS = {
            "DDI":               "⚡",
            "ALLERGY":           "🚨",
            "DOSAGE_ERROR":      "💊",
            "INDICATION_MISMATCH":"🔍",
            "LASA":              "🔤",
        }
        
        for err in sorted(errors, key=lambda x:
                          {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}
                          .get(x["severity"],4)):
            sev  = err["severity"]
            etype = err["error_type"]
            icon  = TYPE_ICONS.get(etype, "⚠️")
            cls   = f"card-{sev.lower()}" if sev in ("CRITICAL","HIGH","MEDIUM") else "card-high"
            
            color_map = {"CRITICAL":"#ef4444","HIGH":"#f97316",
                         "MEDIUM":"#eab308","LOW":"#60a5fa"}
            sev_color = color_map.get(sev,"#60a5fa")
            
            with st.expander(
                f"{icon} [{sev}] {etype.replace('_',' ')} — "
                f"{err.get('message','')[:70]}",
                expanded=(sev=="CRITICAL")
            ):
                cols = st.columns([1,2])
                with cols[0]:
                    st.markdown(
                        f'<div style="background:#111827;border-radius:10px;'
                        f'padding:1rem;text-align:center">'
                        f'<div style="font-size:2rem">{icon}</div>'
                        f'<div style="color:{sev_color};font-weight:700;'
                        f'font-size:1.1rem">{sev}</div>'
                        f'<div style="color:#6b7280;font-size:0.8rem">'
                        f'{etype.replace("_"," ")}</div>'
                        f'</div>', unsafe_allow_html=True
                    )
                    conf = err.get("confidence",0)
                    if conf:
                        st.progress(float(conf),
                                    text=f"Confidence: {int(conf*100)}%")
                
                with cols[1]:
                    if err.get("explanation"):
                        st.markdown("**📋 What happened:**")
                        st.info(err["explanation"])
                    if err.get("solution"):
                        st.markdown("**✅ Recommended Action:**")
                        st.success(err["solution"])
                    if err.get("drug_a") and err.get("drug_b"):
                        st.markdown(
                            f'**Interaction:** `{err["drug_a"]}` + `{err["drug_b"]}`'
                        )
                    if err.get("details"):
                        with st.expander("🔢 Technical Details"):
                            st.json(err["details"])
    
    else:
        st.markdown("""
        <div style="background:#064e3b;border:1px solid #065f46;
                    border-radius:12px;padding:2rem;text-align:center;
                    margin:1rem 0">
          <div style="font-size:3rem">✅</div>
          <div style="color:#6ee7b7;font-size:1.3rem;font-weight:700;
                      margin-top:0.5rem">Prescription Appears Safe</div>
          <div style="color:#059669;margin-top:0.3rem">
            No drug interactions, allergy conflicts, dosage errors, 
            or LASA risks detected.
          </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ── Clear button ──────────────────────────────────────────────────────
    if st.button("🔄 Analyze Another Prescription", use_container_width=True):
        for k in ["result","drug_list","resolved","demo_text"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
