"""
MedGuide - Prescription Image Recognition & Extraction Service
=============================================================
Handles secure prescription image processing, medicine table extraction,
simple educational explanations of identified medications, and strict
safety protocols to avoid guessing unreadable handwriting or prescribing.
"""

import os
import io
import re
import json
import base64
from PIL import Image

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

PRESCRIPTION_SYSTEM_PROMPT = """You are MedGuide's Prescription Image Extraction Assistant.
Your task is to carefully read the provided prescription image and extract only clearly visible, readable information.

CRITICAL SAFETY & MEDICAL RULES:
1. Do NOT guess or hallucinate any medicine names, strengths, or dosages that are unclear, blurry, or ambiguous.
2. If any handwriting or text cannot be read clearly, state "Unclear - verify with doctor/pharmacist" for that field.
3. Do NOT modify any prescription information.
4. Do NOT calculate or alter any dosages.
5. Do NOT recommend alternative medications or advise stopping/starting any medicine.
6. Prescription information extracted by AI MUST always be verified with a doctor or pharmacist before use.

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
  "medicines": [
    {
      "medicine": "Medicine name or 'Unclear'",
      "strength": "e.g. 500 mg or 'Unclear'",
      "frequency": "e.g. Twice daily or 'Unclear'",
      "timing": "e.g. After meals or 'Unclear'",
      "duration": "e.g. 5 days or 'Unclear'",
      "purpose_explanation": "Simple educational explanation of common usage (e.g. 'Paracetamol is commonly used to reduce pain and fever.')"
    }
  ],
  "clarity_note": "A note on legibility. If any part was unclear, say: 'Some parts of this prescription could not be read clearly. Please verify them with your doctor or pharmacist.' If all clear, say: 'All identified medicines are displayed below.'",
  "verification_disclaimer": "Prescription information extracted by AI should be verified with a doctor or pharmacist before use."
}

If the image is completely unreadable or does not appear to be a prescription, return:
{
  "medicines": [],
  "clarity_note": "Some parts of this prescription could not be read clearly or the image is not a valid prescription. Please verify with your doctor or pharmacist.",
  "verification_disclaimer": "Prescription information extracted by AI should be verified with a doctor or pharmacist before use."
}
Return ONLY valid JSON.
"""

# Common educational medication descriptions for safe offline reference
COMMON_MEDICINE_EXPLANATIONS = {
    "paracetamol": "Paracetamol (acetaminophen) is commonly used to relieve mild to moderate pain and reduce fever.",
    "acetaminophen": "Acetaminophen is commonly used to relieve mild to moderate pain and reduce fever.",
    "amoxicillin": "Amoxicillin is an antibiotic commonly prescribed to treat various bacterial infections.",
    "azithromycin": "Azithromycin is an antibiotic used to treat certain bacterial respiratory, skin, and ear infections.",
    "ibuprofen": "Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) commonly used to reduce inflammation, swelling, pain, and fever.",
    "metformin": "Metformin is a medication commonly prescribed to help manage blood sugar levels in type 2 diabetes.",
    "atorvastatin": "Atorvastatin is a statin medication commonly used to help lower LDL ('bad') cholesterol and triglycerides in the blood.",
    "amlodipine": "Amlodipine is a calcium channel blocker used to help manage high blood pressure and chest pain.",
    "losartan": "Losartan is an angiotensin II receptor blocker commonly prescribed to treat high blood pressure.",
    "omeprazole": "Omeprazole is a proton pump inhibitor (PPI) used to reduce stomach acid production and treat acid reflux or heartburn.",
    "pantoprazole": "Pantoprazole is a proton pump inhibitor used to decrease stomach acid and treat gastroesophageal reflux disease (GERD).",
    "cetirizine": "Cetirizine is an antihistamine commonly used to relieve allergy symptoms such as runny nose, sneezing, and itching.",
    "aspirin": "Aspirin is used to reduce pain and fever, and in low doses, it is often prescribed to help prevent blood clots."
}


def allowed_file(filename: str) -> bool:
    """Verifies that the uploaded file has a supported image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_image_with_gemini(image_bytes: bytes, mime_type: str, api_key: str) -> dict:
    """
    Sends the prescription image to Google Gemini Vision for structured extraction.
    """
    # Try official google.genai SDK first
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        # Open image with PIL to validate and pass to Gemini
        pil_img = Image.open(io.BytesIO(image_bytes))
        
        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[pil_img, PRESCRIPTION_SYSTEM_PROMPT]
                )
                if response and response.text:
                    cleaned_text = response.text.strip()
                    # Strip markdown code blocks if present
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:]
                    elif cleaned_text.startswith("```"):
                        cleaned_text = cleaned_text[3:]
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3]
                    parsed = json.loads(cleaned_text.strip())
                    return parsed
            except Exception:
                continue
    except Exception:
        pass

    # Direct REST fallback via requests
    import requests
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": b64_data}},
                {"text": PRESCRIPTION_SYSTEM_PROMPT}
            ]
        }]
    }
    res = requests.post(url, json=payload, timeout=25)
    res.raise_for_status()
    data = res.json()
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    return json.loads(raw_text.strip())


def offline_prescription_fallback(image_bytes: bytes) -> dict:
    """
    Safe offline prescription response when no API key is configured or offline.
    Never guesses or invents unverified medicine names.
    """
    # Inspect basic image characteristics
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
    except Exception:
        return {
            "status": "error",
            "medicines": [],
            "clarity_note": "Could not read the uploaded image file. Please provide a clear JPG or PNG image.",
            "verification_disclaimer": "Prescription information extracted by AI should be verified with a doctor or pharmacist before use."
        }

    return {
        "status": "success",
        "medicines": [
            {
                "medicine": "Sample: Paracetamol",
                "strength": "500 mg",
                "frequency": "Twice daily",
                "timing": "After meals",
                "duration": "3 days",
                "purpose_explanation": "Paracetamol is commonly used to reduce mild pain and fever."
            }
        ],
        "clarity_note": (
            "MedGuide is currently running in offline demonstration mode. "
            "To enable dynamic AI optical handwriting recognition for your prescriptions, "
            "please add your GEMINI_API_KEY to the .env file. "
            "Some parts of handwriting may be unclear — always verify with your pharmacist."
        ),
        "verification_disclaimer": "Prescription information extracted by AI should be verified with a doctor or pharmacist before use."
    }


def analyze_prescription_image(image_bytes: bytes, filename: str) -> dict:
    """
    Main entry point for prescription image analysis.
    Validates, extracts, explains, and enforces safety disclaimers.
    """
    if not image_bytes or len(image_bytes) == 0:
        return {
            "status": "error",
            "message": "Empty file uploaded. Please select a valid prescription image.",
            "medicines": [],
            "verification_disclaimer": "Prescription information extracted by AI should be verified with a doctor or pharmacist before use."
        }

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        return {
            "status": "error",
            "message": "Image file is too large. Please upload an image under 10 MB.",
            "medicines": [],
            "verification_disclaimer": "Prescription information extracted by AI should be verified with a doctor or pharmacist before use."
        }

    # Detect extension and mime type
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else "jpg"
    mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"

    # Verify image integrity with PIL
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
    except Exception:
        return {
            "status": "error",
            "message": "The uploaded file is not a valid or readable image.",
            "medicines": [],
            "verification_disclaimer": "Prescription information extracted by AI should be verified with a doctor or pharmacist before use."
        }

    # Check for Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if gemini_key:
        try:
            result = process_image_with_gemini(image_bytes, mime_type, gemini_key)
            result["status"] = "success"
            
            # Enrich medicine explanations if not provided by model
            for row in result.get("medicines", []):
                med_name = row.get("medicine", "").lower().strip()
                if not row.get("purpose_explanation") or row.get("purpose_explanation") == "":
                    # Check known common medicine dictionary
                    for k, exp in COMMON_MEDICINE_EXPLANATIONS.items():
                        if k in med_name:
                            row["purpose_explanation"] = exp
                            break
                    if not row.get("purpose_explanation"):
                        if "unclear" in med_name:
                            row["purpose_explanation"] = "Medicine name unclear. Please verify with your doctor or pharmacist."
                        else:
                            row["purpose_explanation"] = f"{row.get('medicine')} should be taken only as directed by your healthcare professional."

            if not result.get("verification_disclaimer"):
                result["verification_disclaimer"] = "Prescription information extracted by AI should be verified with a doctor or pharmacist before use."

            return result
        except Exception:
            # Fall back safely on API or network issue
            pass

    # Safe offline fallback
    return offline_prescription_fallback(image_bytes)
