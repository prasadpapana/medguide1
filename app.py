"""
MedGuide - Medical Report Language Simplifier & AI Assistant
===========================================================
Flask Backend Application providing:
- Medical Report Language Explanation (/simplify)
- AI Medical-Language Chatbot (/chat)
- Prescription Image Recognition & Extraction (/analyze-prescription)
- General Educational Food & Nutrition Information (/food-suggestions)
- Medical Report TXT & PDF File Upload (/upload-report)
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from ai_service import (
    simplify_medical_text,
    chat_with_gemini,
    get_food_suggestions,
    extract_text_from_file
)
from prescription_service import analyze_prescription_image, allowed_file

# Load environment variables (.env)
load_dotenv()

app = Flask(__name__)
# Maximum file upload size: 16 MB
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


@app.route("/")
def home():
    """Renders the main MedGuide user interface."""
    return render_template("index.html")


@app.route("/simplify", methods=["POST"])
def simplify():
    """
    Explains difficult medical terms, reports, doctor statements, and lab values
    in patient-friendly simple English with Meaning, In simple words, Example, and Note.
    """
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "result": "Invalid request. Please provide medical report text.",
                "is_medical": False
            }), 400

        report = data.get("report", "")
        if not isinstance(report, str) or not report.strip():
            return jsonify({
                "status": "error",
                "result": "Please enter a medical report or medical text.",
                "is_medical": False
            }), 400

        explanation_data = simplify_medical_text(report)
        return jsonify(explanation_data)

    except Exception:
        return jsonify({
            "status": "error",
            "result": "AI explanation service is currently unavailable. Please check the AI configuration.",
            "is_medical": False
        }), 500


@app.route("/chat", methods=["POST"])
def chat():
    """
    AI Medical Chatbot endpoint:
    Explains medical terms, questions, and concepts in simple English.
    Strictly avoids diagnosis, prescribing, or emergency treatment.
    """
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "response": "Invalid request. Please provide a message."
            }), 400

        message = data.get("message", "")
        history = data.get("history", [])

        if not isinstance(message, str) or not message.strip():
            return jsonify({
                "status": "error",
                "response": "Please enter a question or medical term."
            }), 400

        chat_result = chat_with_gemini(message, history)
        return jsonify(chat_result)

    except Exception:
        return jsonify({
            "status": "error",
            "response": "AI Chat service is temporarily unavailable. Please try again shortly."
        }), 500


@app.route("/analyze-prescription", methods=["POST"])
def analyze_prescription():
    """
    Receives an uploaded prescription image (JPG, PNG, WEBP),
    extracts medicines, dosage, timing, duration into a structured table,
    and explains each clearly identified medicine safely.
    """
    try:
        if "prescription_image" not in request.files:
            return jsonify({
                "status": "error",
                "message": "No prescription image was uploaded."
            }), 400

        file = request.files["prescription_image"]
        if file.filename == "":
            return jsonify({
                "status": "error",
                "message": "Please select a prescription image file to upload."
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                "status": "error",
                "message": "Unsupported file format. Please upload a JPG, JPEG, PNG, or WEBP image."
            }), 400

        image_bytes = file.read()
        analysis = analyze_prescription_image(image_bytes, file.filename)
        return jsonify(analysis)

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Could not analyze the prescription image. Please ensure the image is clear and try again."
        }), 500


@app.route("/food-suggestions", methods=["POST"])
def food_suggestions():
    """
    Provides general educational healthy-eating principles.
    Enforces that food suggestions are NOT a personalized medical diet or cure.
    """
    try:
        data = request.get_json(silent=True) or {}
        topic = data.get("topic", "") or data.get("query", "")

        suggestions = get_food_suggestions(topic)
        return jsonify(suggestions)

    except Exception:
        return jsonify({
            "status": "error",
            "title": "General Nutrition Guidance",
            "content": "Focus on a balanced variety of vegetables, fruits, whole grains, lean proteins, and hydration.",
            "disclaimer": "These are general food and nutrition suggestions, not a personalized medical diet."
        }), 500


@app.route("/upload-report", methods=["POST"])
def upload_report():
    """
    Extracts text from uploaded medical report files (.txt or .pdf).
    """
    try:
        if "report_file" not in request.files:
            return jsonify({
                "status": "error",
                "message": "No file was uploaded."
            }), 400

        file = request.files["report_file"]
        if file.filename == "":
            return jsonify({
                "status": "error",
                "message": "Please select a file to upload."
            }), 400

        file_bytes = file.read()
        extracted = extract_text_from_file(file_bytes, file.filename)
        return jsonify(extracted)

    except Exception:
        return jsonify({
            "status": "error",
            "message": "An error occurred while reading the report file. Please copy and paste the text directly."
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)