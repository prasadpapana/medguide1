"""
MedGuide - AI & NLP Medical Language Understanding & Chatbot Service
===================================================================
This module provides:
1. Dynamic medical report simplification via Google Gemini API
2. Interactive AI Medical Chatbot for medical language understanding
3. Educational general food and nutrition suggestions
4. Secure medical report document text extraction (.txt, .pdf)
5. Comprehensive safety guardrails (no diagnosis, no prescribing, emergency advisories)
6. Multi-model resilience engine with connection pooling and fast fallbacks
"""

import os
import re
import json
import io
import time
import requests
from dotenv import load_dotenv

# Load environment variables (.env)
load_dotenv()

# System prompt for Report Simplification & Natural Medical Questions
REPORT_SYSTEM_PROMPT = """You are MedGuide, an expert AI medical language explanation assistant.
Your job is to understand natural-language medical questions, medical terminology, doctor notes, lab tests, ultrasound/imaging findings, prescriptions, and health/nutrition questions, and explain them in patient-friendly simple English.

CRITICAL INSTRUCTIONS:
1. INTENT & DOMAIN CLASSIFICATION:
   - If the user query is completely NON-MEDICAL and unrelated to health, medicine, biology, wellness, anatomy, nutrition, or medical reports (e.g., programming like 'How to write a Java program?', math, trivia, general sports, general tech, jokes, recipes):
     Respond EXACTLY with:
     This assistant is designed for medical-language understanding. Please enter a medical term, medical report sentence, prescription-related question, or health-information question.

2. MEDICAL & HEALTH EXPLANATIONS:
   - If the user query IS related to health, medicine, medical reports, symptoms, conditions, lab tests, scans, or nutrition (e.g., 'What is migraine mean?', 'The ultrasound report describes a small gallstone', 'Explain microscopic hematuria', 'What food is generally associated with heart-healthy eating?'):
     Explain it clearly and dynamically using EXACTLY this structured format:

Meaning:
[Clear, simple definition of the medical term, question, or finding.]

In simple words:
[Everyday language explanation that anyone can easily understand.]

Example:
[A helpful, educational real-world context or example.]

Important note:
This explanation is for educational understanding and is not a medical diagnosis. Always consult a qualified healthcare professional for medical advice.

3. SAFETY RULES:
   - Do NOT diagnose or tell a user they definitely have a condition.
   - Do NOT prescribe or recommend changing medications/dosages.
   - Do NOT replace a doctor or give emergency self-treatment instructions.
   - Use objective, patient-friendly phrasing ('may mean', 'is often associated with').
"""

# System prompt for the Interactive Medical Chatbot
CHAT_SYSTEM_PROMPT = """You are MedGuide's AI Medical Assistant, dedicated to helping people understand medical language, doctor explanations, lab terminology, ultrasound/scan reports, and health concepts in simple, easy English.

CRITICAL INSTRUCTIONS:
1. MEDICAL & HEALTH QUESTIONS:
   - Understand natural-language medical questions and variations (e.g., 'What is migraine mean?', 'Explain thrombocytopenia', 'The scan shows a small gallstone', 'What food is good for the heart?').
   - For any medical term, report finding, or health concept, explain it clearly using:
     **Meaning:** Simple definition.
     **In simple words:** Everyday easy explanation.
     **Example:** Helpful educational example or context when useful.
     **Important note:** This explanation is for educational understanding and is not a medical diagnosis. Always consult a qualified healthcare professional for medical advice.

2. STRICT SAFETY & ETHICAL BOUNDARIES:
   - NOT A DOCTOR: You do NOT diagnose medical conditions, prescribe medicines, or provide personalized treatment plans.
   - NO PRESCRIPTIONS: If asked 'What medicine should I take for this?' or similar, refuse safely:
     "I can help explain medical terms and health concepts, but I cannot prescribe medication or recommend treatments. Please consult a qualified healthcare professional for personalized medical advice."
   - NO DIAGNOSIS: If asked for a definitive personal diagnosis ('Do I have this disease?'):
     "I can help explain the medical information in simple language, but I cannot diagnose a condition or provide treatment instructions. Please consult a qualified healthcare professional for medical advice."
   - EMERGENCY CARE: If the user mentions acute red-flag emergency symptoms (severe chest pain, difficulty breathing, sudden paralysis, coughing blood, severe bleeding):
     "Some symptoms can require urgent medical attention. Please contact a qualified healthcare professional or local emergency service promptly rather than relying on this application."
   - FOOD & NUTRITION: If asked if a food cures disease, clarify that food supports general health but is not a medical cure.

3. NON-MEDICAL QUESTIONS:
   - If the user asks something completely non-medical (e.g., 'How to write a Java program?', 'Capital of France'):
     "This assistant is designed for medical-language understanding. Please enter a medical term, medical report sentence, prescription-related question, or health-information question."

Always explain concepts with beginner-friendly, compassionate, and crystal-clear English.
"""

# Knowledge Base for Offline Emergency Fallback Mode
OFFLINE_TERMS = {
    "anemia": {
        "meaning": "Anemia means your blood does not have enough healthy red blood cells or hemoglobin to carry oxygen effectively throughout your body.",
        "in_simple_words": "Your blood may not be carrying enough oxygen around your body.",
        "example": "This can sometimes cause tiredness, weakness, or shortness of breath."
    },
    "thrombocytopenia": {
        "meaning": "Thrombocytopenia means the platelet count in the blood is lower than the normal range.",
        "in_simple_words": "There are fewer platelets than usual. Platelets help the blood form clots to stop bleeding.",
        "example": "A person with a low platelet count may need the result interpreted together with other medical information, as it can sometimes be associated with easier bruising.",
    },
    "hypertension": {
        "meaning": "Hypertension is the medical term for high or elevated blood pressure, where blood pushes against artery walls with higher force than normal.",
        "in_simple_words": "Your heart has to work harder than usual to pump blood through your blood vessels.",
        "example": "High blood pressure often has no symptoms initially, which is why routine blood pressure checks are important."
    },
    "hypotension": {
        "meaning": "Hypotension is the medical term for low blood pressure, where blood flows through vessels at lower pressure than typical ranges.",
        "in_simple_words": "Blood is moving through your body with less pressure than usual.",
        "example": "It can sometimes cause temporary dizziness, lightheadedness, or feeling faint when standing up quickly."
    },
    "hyperglycemia": {
        "meaning": "Hyperglycemia means having an abnormally high level of glucose (sugar) circulating in the bloodstream.",
        "in_simple_words": "There is more sugar in your blood than the body typically maintains.",
        "example": "It can be associated with increased thirst, frequent urination, and fatigue."
    },
    "hypoglycemia": {
        "meaning": "Hypoglycemia means having an abnormally low level of glucose (sugar) in the bloodstream.",
        "in_simple_words": "Your blood sugar has dropped below the normal level needed for energy.",
        "example": "It can cause shakiness, sweating, sudden hunger, dizziness, or a fast heartbeat."
    },
    "hemoglobin": {
        "meaning": "Hemoglobin is an iron-rich protein in red blood cells that carries oxygen from your lungs to tissues throughout your body.",
        "in_simple_words": "It is the oxygen carrier in your blood that helps keep your body energized.",
        "example": "When hemoglobin levels are lower than normal, a person may feel unusually tired or weak."
    },
    "inflammation": {
        "meaning": "Inflammation is your body's immune response to an injury, irritation, or infection.",
        "in_simple_words": "It is your body's defense system working to protect and repair damaged tissues.",
        "example": "Common signs can include swelling, redness, warmth, or mild discomfort in the affected area."
    },
    "elevated cholesterol": {
        "meaning": "Elevated cholesterol (hypercholesterolemia) means there is a higher-than-recommended amount of cholesterol fat circulating in the bloodstream.",
        "in_simple_words": "There is extra fat circulating in your bloodstream.",
        "example": "Doctors often recommend lifestyle adjustments, dietary changes, or medications to keep cardiovascular health optimal."
    },
    "cholesterol": {
        "meaning": "Cholesterol is a waxy, fat-like substance found in your blood that your body uses to build cells and produce hormones.",
        "in_simple_words": "It is a type of fat in your blood that needs to remain in healthy balance.",
        "example": "Having elevated levels of LDL (often called 'bad cholesterol') can gradually build up in artery walls."
    },
    "tachycardia": {
        "meaning": "Tachycardia refers to a resting heart rate that is faster than normal, typically exceeding 100 beats per minute in adults.",
        "in_simple_words": "Your heart is beating faster than usual while at rest.",
        "example": "It can occur during physical exertion, stress, fever, dehydration, or certain heart conditions."
    },
    "bradycardia": {
        "meaning": "Bradycardia refers to a resting heart rate that is slower than normal, typically below 60 beats per minute in adults.",
        "in_simple_words": "Your heart is beating more slowly than the typical resting speed.",
        "example": "It can be normal in athletic individuals, or can sometimes cause fatigue and dizziness in others."
    },
    "creatinine": {
        "meaning": "Creatinine is a waste product produced by normal muscle breakdown, filtered from the blood and excreted by healthy kidneys.",
        "in_simple_words": "It is a natural waste substance in your blood that doctors measure to check how well your kidneys are filtering.",
        "example": "Doctors compare blood creatinine levels to typical reference ranges to assess overall kidney function."
    },
    "alt": {
        "meaning": "ALT (alanine aminotransferase) is an enzyme found primarily inside liver cells that helps process proteins.",
        "in_simple_words": "It is a protein found inside liver cells that enters the bloodstream if liver cells are stressed or irritated.",
        "example": "An elevated ALT reading on a liver panel prompts doctors to check for things like medications, fatty liver, or infections."
    },
    "tsh": {
        "meaning": "TSH (thyroid-stimulating hormone) is produced by the pituitary gland to regulate the amount of hormones the thyroid gland produces.",
        "in_simple_words": "It is a messenger hormone from your brain telling your thyroid gland how much energy-regulating hormone to make.",
        "example": "Higher or lower TSH values can indicate that the thyroid gland is producing less or more hormone than typical."
    }
}

STANDARD_NOTE = (
    "This explanation is for educational understanding and is not a medical diagnosis. "
    "Always consult a qualified healthcare professional for medical advice."
)

NON_MEDICAL_RESPONSE = (
    "This assistant is designed for medical-language understanding. Please enter a medical term, "
    "medical report sentence, prescription-related question, or health-information question."
)

DIAGNOSIS_REFUSAL_RESPONSE = (
    "I can help explain the medical information in simple language, but I cannot diagnose a condition "
    "or provide treatment instructions. Please consult a qualified healthcare professional for medical advice."
)

PRESCRIPTION_REFUSAL_RESPONSE = (
    "I can help explain medical terms and health concepts, but I cannot prescribe medication, recommend "
    "changing medicine dosage, or provide treatment instructions. Please consult a qualified healthcare professional "
    "or pharmacist for personalized medical advice."
)

EMERGENCY_RESPONSE = (
    "Some symptoms can require urgent medical attention. Please contact a qualified healthcare professional "
    "or local emergency service promptly rather than relying on this application."
)

FOOD_CURE_REFUSAL = (
    "Food can support general health, but it should not be considered a cure. For a personalized diet plan, "
    "consult a qualified doctor or registered dietitian."
)

# Active, supported Gemini models in priority order
GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest"
]

# Track last known healthy model to maximize first-request & ongoing speed
_ACTIVE_WORKING_MODEL = GEMINI_MODELS[0]

# Persistent HTTP session for connection pooling
_HTTP_SESSION = requests.Session()


def is_emergency_query(text: str) -> bool:
    """Detects high-risk acute emergency phrases."""
    cleaned = text.lower()
    emergency_patterns = [
        r"severe chest pain", r"heart attack", r"can'?t breathe", r"difficulty breathing",
        r"sudden numbness", r"slurred speech", r"face drooping",
        r"coughing (?:up )?blood", r"severe bleeding", r"unconscious", r"collapsed",
        r"poisoning", r"swallowed bleach", r"overdose"
    ]
    return any(re.search(p, cleaned) for p in emergency_patterns)


def is_prescription_request(text: str) -> bool:
    """Detects requests asking for medicine prescriptions, dosages, or self-medication."""
    cleaned = text.lower()
    patterns = [
        r"what medicine should i take", r"which medicine should i take",
        r"can you prescribe", r"give me a prescription", r"what dose should i take",
        r"how many pills should i take", r"can i stop taking", r"should i change my dose",
        r"what drug should i take", r"recommend a medicine"
    ]
    return any(re.search(p, cleaned) for p in patterns)


def is_diagnosis_request(text: str) -> bool:
    """Detects requests asking for definitive clinical diagnosis."""
    cleaned = text.lower()
    patterns = [
        r"do i have (?:cancer|diabetes|covid|asthma|a disease|a condition)",
        r"diagnose me", r"what disease do i have", r"tell me what is wrong with me",
        r"do i definitely have"
    ]
    return any(re.search(p, cleaned) for p in patterns)


def format_explanation_response(meaning: str, simple_words: str, example: str, note: str = STANDARD_NOTE) -> dict:
    """Builds a standardized 4-part explanation payload."""
    full_text = (
        f"Meaning:\n{meaning}\n\n"
        f"In simple words:\n{simple_words}\n\n"
        f"Example:\n{example}\n\n"
        f"Important note:\n{note}"
    )
    return {
        "status": "success",
        "type": "medical_explanation",
        "result": full_text,
        "is_medical": True,
        "structured": {
            "meaning": meaning,
            "in_simple_words": simple_words,
            "example": example,
            "important_note": note
        }
    }


def call_gemini(prompt: str, system_instruction: str = REPORT_SYSTEM_PROMPT, enable_search: bool = False) -> tuple[str | None, str | None]:
    """
    Invokes Google Gemini API with multi-model resilience, connection reuse, and proper error handling.
    Returns (response_text, error_code).
    """
    global _ACTIVE_WORKING_MODEL

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, "NO_API_KEY"

    # Order models putting the last successful one first
    ordered_models = [_ACTIVE_WORKING_MODEL] + [m for m in GEMINI_MODELS if m != _ACTIVE_WORKING_MODEL]

    # 1. Try google.genai SDK if available
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for model_name in ordered_models:
            try:
                full_contents = f"{system_instruction}\n\nUser Input:\n\"{prompt}\""
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_contents
                )
                if response and response.text:
                    _ACTIVE_WORKING_MODEL = model_name
                    return response.text.strip(), None
            except Exception as sdk_err:
                err_str = str(sdk_err)
                # If 404 or 429 or quota exceeded, try next model
                if "404" in err_str or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    continue
                # For other errors, continue to fallback
                continue
    except Exception:
        pass

    # 2. Resilient Direct REST API with Connection Pooling
    for model_name in ordered_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_instruction}\n\nUser Input:\n\"{prompt}\""}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024
            }
        }
        
        # Optionally try search grounding if requested
        if enable_search:
            payload["tools"] = [{"googleSearch": {}}]

        for attempt in range(2):
            try:
                res = _HTTP_SESSION.post(url, json=payload, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            _ACTIVE_WORKING_MODEL = model_name
                            return parts[0]["text"].strip(), None
                elif res.status_code == 429:
                    # Rate limit or quota exceeded for this model -> jump to next model
                    break
                elif res.status_code == 404:
                    # Model not found -> jump to next model
                    break
                elif res.status_code >= 500:
                    time.sleep(0.5)
                    continue
            except requests.exceptions.Timeout:
                # Timeout -> try next model
                break
            except Exception:
                break

    return None, "API_FAILURE"


def parse_llm_response(raw_text: str) -> dict:
    """Parses raw LLM generation into structured output for frontend display & speech."""
    text = raw_text.strip()

    # Non-medical intent detection
    if "this assistant is designed for medical-language" in text.lower() or "does not appear to be medical" in text.lower():
        return {
            "status": "success",
            "type": "non_medical",
            "result": NON_MEDICAL_RESPONSE,
            "is_medical": False
        }

    # Unrecognized term detection (when Gemini explicitly states the term is unrecognizable)
    if "couldn't confidently identify" in text.lower() or "could not confidently identify" in text.lower():
        return {
            "status": "success",
            "type": "unrecognized",
            "result": "I couldn't confidently identify this medical term. Please check the spelling or ask your healthcare professional for clarification.",
            "is_medical": False
        }

    # Structured 4-part extraction
    meaning_match = re.search(r"Meaning:\s*(.*?)(?=\n\s*(?:In simple words|Example|Important note):|$)", text, re.DOTALL | re.IGNORECASE)
    simple_match = re.search(r"In simple words:\s*(.*?)(?=\n\s*(?:Example|Important note):|$)", text, re.DOTALL | re.IGNORECASE)
    example_match = re.search(r"Example:\s*(.*?)(?=\n\s*Important note:|$)", text, re.DOTALL | re.IGNORECASE)
    note_match = re.search(r"Important note:\s*(.*?)$", text, re.DOTALL | re.IGNORECASE)

    if meaning_match and simple_match:
        meaning = meaning_match.group(1).strip()
        simple_words = simple_match.group(1).strip()
        example = example_match.group(1).strip() if example_match else "Your doctor can explain how this applies to your specific report."
        note = note_match.group(1).strip() if note_match else STANDARD_NOTE
        return format_explanation_response(meaning, simple_words, example, note)

    # Fallback to general medical text if headings weren't cleanly separated
    return {
        "status": "success",
        "type": "medical_explanation",
        "result": text,
        "is_medical": True
    }


def simplify_medical_text(text: str) -> dict:
    """
    Main entry point for medical report simplification.
    Uses Gemini to dynamically understand questions, terms, statements, and scan findings.
    """
    if not text or not text.strip():
        return {
            "status": "error",
            "type": "empty_input",
            "result": "Please enter a medical report or medical text.",
            "is_medical": False
        }

    cleaned = text.strip()
    if len(cleaned) > 10000:
        return {
            "status": "error",
            "type": "length_exceeded",
            "result": "Input is too long. Please enter a report under 10,000 characters.",
            "is_medical": False
        }

    # Safety: Emergency check
    if is_emergency_query(cleaned):
        return {
            "status": "success",
            "type": "emergency",
            "result": EMERGENCY_RESPONSE,
            "is_medical": True
        }

    # Process dynamically via Gemini AI
    ai_raw, err_code = call_gemini(cleaned, REPORT_SYSTEM_PROMPT)
    if ai_raw:
        res = parse_llm_response(ai_raw)
        res["source"] = "gemini_api"
        return res

    # Offline Emergency Fallback (ONLY when API fails/is unreachable)
    cleaned_lower = cleaned.lower()
    for term in sorted(OFFLINE_TERMS.keys(), key=lambda x: len(x), reverse=True):
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, cleaned_lower):
            data = OFFLINE_TERMS[term]
            res = format_explanation_response(data["meaning"], data["in_simple_words"], data["example"])
            res["source"] = "offline_fallback"
            return res

    # If the API genuinely failed, return a proper service error rather than claiming unrecognized term
    return {
        "status": "error",
        "type": "api_unavailable",
        "result": "AI explanation service is temporarily unavailable. Please try again shortly.",
        "is_medical": False
    }


def chat_with_gemini(user_message: str, chat_history: list = None) -> dict:
    """
    Handles interactive conversations with MedGuide's AI Medical Assistant.
    Understands natural medical questions, terms, and conversational follow-ups.
    """
    if not user_message or not user_message.strip():
        return {
            "status": "error",
            "response": "Please enter a question or medical term."
        }

    cleaned = user_message.strip()

    # 1. Emergency safety check
    if is_emergency_query(cleaned):
        return {
            "status": "success",
            "response": EMERGENCY_RESPONSE,
            "category": "emergency"
        }

    # 2. Prescription request refusal
    if is_prescription_request(cleaned):
        return {
            "status": "success",
            "response": PRESCRIPTION_REFUSAL_RESPONSE,
            "category": "prescription_refusal"
        }

    # 3. Diagnosis request refusal
    if is_diagnosis_request(cleaned):
        return {
            "status": "success",
            "response": DIAGNOSIS_REFUSAL_RESPONSE,
            "category": "diagnosis_refusal"
        }

    # 4. Build conversation context
    history_context = ""
    if chat_history and isinstance(chat_history, list):
        for turn in chat_history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            history_context += f"{role.capitalize()}: {content}\n"

    full_prompt = f"{history_context}User: {cleaned}\nAI Assistant:"
    
    # 5. Dynamic Gemini Understanding
    ai_raw, err_code = call_gemini(full_prompt, CHAT_SYSTEM_PROMPT)
    if ai_raw:
        return {
            "status": "success",
            "response": ai_raw,
            "category": "ai_chat",
            "source": "gemini_api"
        }

    # 6. Offline Knowledge Fallback (Only on complete API outage)
    cleaned_lower = cleaned.lower()
    for term, data in OFFLINE_TERMS.items():
        if term in cleaned_lower:
            return {
                "status": "success",
                "response": (
                    f"**{term.capitalize()}**:\n\n"
                    f"**Meaning:** {data['meaning']}\n\n"
                    f"**In simple words:** {data['in_simple_words']}\n\n"
                    f"**Example:** {data['example']}\n\n"
                    f"**Important note:** {STANDARD_NOTE}"
                ),
                "category": "offline_explanation",
                "source": "offline_fallback"
            }

    # 7. When API is down and term is not in minimal offline dictionary
    return {
        "status": "error",
        "response": "AI Chat service is temporarily unavailable. Please try again shortly.",
        "category": "service_unavailable"
    }


def get_food_suggestions(query_or_topic: str) -> dict:
    """
    Provides general educational nutrition information strictly separated from personalized medical diets.
    """
    topic = (query_or_topic or "").strip().lower()

    if "cure" in topic:
        return {
            "status": "success",
            "title": "General Nutrition Guidance",
            "content": FOOD_CURE_REFUSAL,
            "disclaimer": "These are general food and nutrition suggestions, not a personalized medical diet."
        }

    prompt = (
        f"Provide general educational nutrition principles relevant to: '{topic}'. "
        "Strict rules: Never claim any food cures disease. Do NOT give personalized medical meal plans. "
        "Emphasize general healthy eating (vegetables, fruits, whole grains, water, balanced portions)."
    )

    ai_raw, err = call_gemini(prompt, CHAT_SYSTEM_PROMPT)
    if ai_raw:
        return {
            "status": "success",
            "title": f"General Nutrition Information ({query_or_topic.capitalize() if query_or_topic else 'Healthy Eating'})",
            "content": ai_raw,
            "disclaimer": "These are general food and nutrition suggestions, not a personalized medical diet."
        }

    content = (
        "General healthy eating principles for overall wellness include:\n"
        "• A wide variety of colorful vegetables and whole fruits\n"
        "• Fiber-rich whole grains (such as oats, brown rice, and whole wheat)\n"
        "• Lean proteins (lentils, beans, tofu, eggs, or fish)\n"
        "• Healthy unsaturated fats (olive oil, nuts, and seeds)\n"
        "• Staying well-hydrated with water throughout the day\n"
        "• Limiting highly processed foods, excess sodium, and refined sugars"
    )

    if "cholesterol" in topic or "heart" in topic:
        content += (
            "\n\nFor general heart-healthy eating, people often focus on soluble fiber (oats, barley, beans), "
            "omega-3 rich foods, and limiting saturated and trans fats."
        )

    return {
        "status": "success",
        "title": "General Healthy Eating Principles",
        "content": content,
        "disclaimer": "These are general food and nutrition suggestions, not a personalized medical diet."
    }


def extract_text_from_file(file_bytes: bytes, filename: str) -> dict:
    """
    Extracts readable medical report text from uploaded TXT or PDF files.
    """
    if not file_bytes or len(file_bytes) == 0:
        return {"status": "error", "message": "Uploaded file is empty."}

    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

    if ext == "txt":
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="ignore")
        return {"status": "success", "text": text.strip()}

    elif ext == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_pages.append(page_text.strip())

            full_text = "\n\n".join(extracted_pages).strip()
            if not full_text:
                return {
                    "status": "warning",
                    "text": "",
                    "message": "The uploaded PDF appears to be a scanned image or empty. Please enter your medical text directly or upload a digital text-based PDF."
                }
            return {"status": "success", "text": full_text}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Could not read the PDF file: {str(e)}. Please paste text directly."
            }

    return {"status": "error", "message": "Unsupported file format. Please upload a .txt or .pdf file."}
