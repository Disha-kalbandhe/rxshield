"""
OCR Pipeline for RxShield
Primary: Gemini Vision API (fast, accurate, cloud-based)
Fallback: Tesseract (when Gemini fails or no API key)

Old approach (TrOCR + line segmentation) was too slow and caused timeouts.
New approach: Gemini Vision API delivers both OCR AND structured extraction in 2-3 seconds.
"""

# ============================================================================
# SECTION 1 — Imports and Configuration
# ============================================================================

import os
import base64
import re
import io
import platform
import json
import google.generativeai as genai
from PIL import Image
import pytesseract
from dotenv import load_dotenv

load_dotenv()

# Set Tesseract path for Windows
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GEMINI_MODEL = "gemini-2.0-flash-exp"
_gemini_model = None


# ============================================================================
# SECTION 2 — Gemini Model Loader (Lazy)
# ============================================================================

def load_gemini():
    """Lazy load Gemini model."""
    global _gemini_model
    if _gemini_model is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in .env")
        _gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        print(f"✅ Gemini {GEMINI_MODEL} loaded for OCR")
    return _gemini_model


# ============================================================================
# SECTION 3 — Gemini Vision OCR (PRIMARY ENGINE)
# ============================================================================

def ocr_with_gemini(image: Image.Image, language: str = "auto") -> dict:
    """
    Uses Gemini Vision to extract prescription text from image.
    Returns both raw text AND structured drug data in one API call.
    
    Args:
        image: PIL Image object
        language: Language hint ("auto", "hindi", "marathi", etc.)
    
    Returns:
        dict with keys: text, engine, language, confidence, structured
    """
    model = load_gemini()
    
    # Convert PIL image to bytes for Gemini
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=95)
    img_bytes = img_byte_arr.getvalue()
    
    # Build language hint
    lang_hint = ""
    if language in ["hindi", "devanagari"]:
        lang_hint = "The prescription may contain Hindi/Devanagari text."
    elif language == "marathi":
        lang_hint = "The prescription may contain Marathi/Devanagari text."
    
    # The prompt — designed specifically for prescription extraction
    prompt = f"""You are a medical prescription OCR system. 
Carefully read ALL text in this prescription image, including handwritten content.
{lang_hint}

Extract everything and return ONLY a valid JSON object (no markdown, no explanation):

{{
  "raw_text": "COMPLETE verbatim text from entire image, preserving line breaks with \\n",
  "patient_name": "patient name or null",
  "patient_age": "age as string or null",
  "patient_address": "address or null",
  "date": "date or null",
  "hospital_clinic": "hospital or clinic name or null",
  "doctor_name": "doctor name or null",
  "drugs": [
    {{
      "name": "drug/medicine name",
      "dose": "dosage e.g. 100mg",
      "frequency": "e.g. twice daily, BID, TID",
      "duration": "e.g. 7 days or null",
      "quantity": "e.g. 1 tab or null"
    }}
  ],
  "special_instructions": "any special notes or instructions or null",
  "language_detected": "english or hindi or marathi or mixed"
}}

Important rules:
- Include ALL drugs mentioned, even if unclear
- For frequency: preserve original abbreviations (BID, TID, QD, etc.)
- raw_text must contain the COMPLETE text exactly as written
- If a field is not visible, use null
- Return ONLY the JSON, no other text"""

    try:
        # Create image part for Gemini
        image_part = {
            "mime_type": "image/jpeg",
            "data": img_bytes
        }
        
        response = model.generate_content(
            [prompt, image_part],
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,      # low temperature = more accurate OCR
                max_output_tokens=2048
            )
        )
        
        raw_response = response.text.strip()
        
        # Clean JSON response (remove markdown code blocks if present)
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_response:
            raw_response = raw_response.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        extracted = json.loads(raw_response)
        
        raw_text = extracted.get("raw_text", "")
        
        return {
            "text": raw_text,
            "engine": "Gemini Vision",
            "language": extracted.get("language_detected", language),
            "confidence": 0.95,   # Gemini is highly reliable
            "structured": {
                "patient_name": extracted.get("patient_name"),
                "patient_age": extracted.get("patient_age"),
                "patient_address": extracted.get("patient_address"),
                "date": extracted.get("date"),
                "hospital_clinic": extracted.get("hospital_clinic"),
                "doctor_name": extracted.get("doctor_name"),
                "drugs": extracted.get("drugs", []),
                "special_instructions": extracted.get("special_instructions")
            }
        }
    
    except json.JSONDecodeError:
        # Gemini returned text but not valid JSON — use raw text anyway
        print(f"  ⚠️ Gemini JSON parse failed, using raw text")
        return {
            "text": raw_response[:1000] if raw_response else "",
            "engine": "Gemini Vision (raw)",
            "language": language,
            "confidence": 0.85,
            "structured": {}
        }
    except Exception as e:
        print(f"  ❌ Gemini OCR error: {e}")
        return None   # triggers fallback


# ============================================================================
# SECTION 4 — Tesseract Fallback
# ============================================================================

def ocr_with_tesseract(image: Image.Image, language: str = "auto") -> dict:
    """
    Tesseract fallback when Gemini fails.
    
    Args:
        image: PIL Image object
        language: Language hint
    
    Returns:
        dict with OCR results
    """
    try:
        import cv2
        import numpy as np
        
        # Quick preprocess
        img_cv = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]
        if w < 1200:
            scale = 1200 / w
            img_cv = cv2.resize(img_cv, None, fx=scale, fy=scale,
                                interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)
        pil_img = Image.fromarray(thresh)
        
        # Language selection
        tess_lang = "eng"
        if language in ["hindi", "devanagari"]:
            tess_lang = "hin+eng"
        elif language == "marathi":
            tess_lang = "mar+eng"
        
        config = r"--oem 3 --psm 6 -c preserve_interword_spaces=1"
        text = pytesseract.image_to_string(pil_img, lang=tess_lang, config=config)
        
        data = pytesseract.image_to_data(pil_img, lang=tess_lang, config=config,
                                          output_type=pytesseract.Output.DICT)
        confs = [int(c) for c in data['conf'] if str(c).isdigit() and int(c) > 0]
        avg_conf = round(sum(confs)/len(confs), 2) if confs else 0
        
        return {
            "text": text.strip(),
            "engine": "Tesseract (fallback)",
            "language": language,
            "confidence": avg_conf,
            "structured": {}
        }
    except Exception as e:
        return {
            "text": "",
            "engine": "error",
            "language": language,
            "confidence": 0,
            "error": str(e),
            "structured": {}
        }


# ============================================================================
# SECTION 5 — Main OCR Function (Replaces old run_ocr)
# ============================================================================

def run_ocr(image: Image.Image, language: str = "auto") -> dict:
    """
    Primary: Gemini Vision (~2-3 sec, highly accurate)
    Fallback: Tesseract (if Gemini fails or no API key)
    
    Args:
        image: PIL Image object
        language: Language hint ("auto", "english", "hindi", "marathi", "devanagari")
    
    Returns:
        dict with OCR results including text, engine, language, confidence, structured
    """
    # Try Gemini first
    if GEMINI_API_KEY:
        print("🤖 Using Gemini Vision for OCR...")
        result = ocr_with_gemini(image, language)
        if result and result.get("text"):
            print(f"  ✅ Gemini extracted {len(result['text'])} chars")
            return result
        print("  ⚠️ Gemini returned empty, falling back to Tesseract...")
    else:
        print("⚠️ No GEMINI_API_KEY found, using Tesseract...")
    
    # Fallback to Tesseract
    print("🔤 Using Tesseract fallback...")
    return ocr_with_tesseract(image, language)


# ============================================================================
# SECTION 6 — Post-processing for prescription text
# ============================================================================

def clean_prescription_text(raw_text: str) -> str:
    """
    Cleans OCR output specifically for medical prescription text.
    Fixes common OCR errors in drug names and dosage notation.
    
    Args:
        raw_text: Raw OCR output text
    
    Returns:
        Cleaned and normalized prescription text
    """
    if not raw_text:
        return ""
    
    text = raw_text
    
    # Remove OCR separator markers
    text = re.sub(r'---+', '\n', text)
    
    # Fix spaced numbers before units: "100 m g" → "100 mg"
    text = re.sub(r'(\d+)\s+m\s*g', r'\1 mg', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s+m\s*l', r'\1 ml', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d+)\s+m\s*c\s*g', r'\1 mcg', text, flags=re.IGNORECASE)
    
    # Fix digit-unit spacing: "100mg" → "100 mg"
    text = re.sub(r'(\d+)(mg|mcg|ml|units?|tabs?|caps?)', 
                  r'\1 \2', text, flags=re.IGNORECASE)
    
    # Normalize frequency abbreviations
    freq_map = {
        r'\bBD\b': 'twice daily',
        r'\bBID\b': 'twice daily',
        r'\bTID\b': 'three times daily',
        r'\bTTD\b': 'three times daily',
        r'\bTDD\b': 'three times daily',
        r'\bQID\b': 'four times daily',
        r'\bQD\b': 'once daily',
        r'\bOD\b': 'once daily',
        r'\bHS\b': 'at bedtime',
        r'\bPRN\b': 'as needed',
        r'\bSOS\b': 'if needed',
        r'\bStat\b': 'immediately',
        r'\bAC\b': 'before meals',
        r'\bPC\b': 'after meals',
    }
    for pattern, replacement in freq_map.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Fix common OCR character confusions in drug names
    ocr_fixes = {
        r'\bBeta1oc\b': 'Betaloc',
        r'\bMetf0rmin\b': 'Metformin',
        r'\bAsp1rin\b': 'Aspirin',
        r'\bAmox1cillin\b': 'Amoxicillin',
        r'\b0mg\b': '0 mg',
        r'\bl\s+tab\b': '1 tab',  # 'l' misread as 1
        r'\bI\s+tab\b': '1 tab',  # 'I' misread as 1
    }
    for pattern, replacement in ocr_fixes.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Clean up lines
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Remove lines that are just punctuation/symbols/single chars
        if len(line) < 2:
            continue
        # Remove lines that are only special characters
        if re.match(r'^[^\w\d]+$', line):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


# ============================================================================
# SECTION 7 — Input Handlers (Base64 and File Path)
# ============================================================================

def ocr_from_base64(image_b64: str, language: str = "auto") -> dict:
    """
    Run OCR on base64-encoded image.
    
    Args:
        image_b64: Base64-encoded image string (with or without data URI prefix)
        language: Target language for OCR
    
    Returns:
        dict with OCR results + cleanedText, charCount, success fields
    """
    try:
        # Strip data URI prefix if present
        if "base64," in image_b64:
            image_b64 = image_b64.split("base64,")[1]
        
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Run OCR
        result = run_ocr(image, language)
        
        # Add cleaned text and metadata
        result["cleanedText"] = clean_prescription_text(result.get("text", ""))
        result["charCount"] = len(result.get("cleanedText", ""))
        result["success"] = len(result.get("cleanedText", "")) > 5
        
        return result
    except Exception as e:
        return {
            "text": "",
            "engine": "error",
            "language": language,
            "confidence": 0,
            "error": str(e),
            "cleanedText": "",
            "charCount": 0,
            "success": False,
            "structured": {}
        }


def ocr_from_file(image_path: str, language: str = "auto") -> dict:
    """
    Run OCR on image file.
    
    Args:
        image_path: Path to image file
        language: Target language for OCR
    
    Returns:
        dict with OCR results + cleanedText, charCount, success fields
    """
    try:
        image = Image.open(image_path).convert("RGB")
        
        # Run OCR
        result = run_ocr(image, language)
        
        # Add cleaned text and metadata
        result["cleanedText"] = clean_prescription_text(result.get("text", ""))
        result["charCount"] = len(result.get("cleanedText", ""))
        result["success"] = len(result.get("cleanedText", "")) > 5
        
        return result
    except Exception as e:
        return {
            "text": "",
            "engine": "error",
            "language": language,
            "confidence": 0,
            "error": str(e),
            "cleanedText": "",
            "charCount": 0,
            "success": False,
            "structured": {}
        }
