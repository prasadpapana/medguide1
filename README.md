# MedGuide - Medical Report Language Simplifier & AI Assistant

MedGuide is a patient-centered AI application designed to translate complex medical jargon, lab test terminology, ultrasound/imaging statements, and doctor notes into simple, clear, and reassuring English.

---

## 🌟 Key Features

1. **Medical Report Language Simplifier:**
   - Dynamically translates complex medical statements, lab values, and diagnostic terminology into simple English.
   - Structured 4-part explanations: **Meaning**, **In simple words**, **Example**, and **Important note**.
   - Multi-model resilient fallback powered by Google Gemini API.

2. **Interactive AI Medical Chatbot:**
   - Answers natural-language medical questions and conversational follow-ups.
   - Distinct classification between medical questions and non-medical topics.

3. **Prescription Vision Analyzer:**
   - Extracts medicines, strengths, frequencies, timings, and durations from uploaded prescription images into a structured summary table.
   - Explains the purpose of each recognized medication.

4. **Educational Nutrition Guidance:**
   - Provides general healthy-eating principles strictly separated from personalized medical diets.

5. **Accessibility Features:**
   - Text-to-Speech (audio explanation readout) and Speech-to-Text (voice input).
   - Medical report file text extraction (.txt and digital .pdf).

6. **Safety First:**
   - Strict ethical guardrails: no clinical diagnosis, no prescribing, and prominent emergency advisories for acute symptoms.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/prasadpapana/medguide1.git
cd medguide1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and add your Gemini API key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Get a free API key from [Google AI Studio](https://aistudio.google.com/))*

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **http://127.0.0.1:5000**

### Deploy to Vercel

Install the [Vercel CLI](https://vercel.com/docs/cli), then run these commands from the project folder:
```bash
vercel login
vercel
```
To deploy a production build, run `vercel --prod`. Add `GEMINI_API_KEY` under the project's Vercel **Settings → Environment Variables** to enable AI features. Do not commit API keys to the repository.

The application serves the Flask UI from `templates/`. Static files remain in `static/` for local Flask runs and are mirrored in `public/static/` for Vercel's CDN.

---

## 🛡️ Privacy & Medical Disclaimer

- **Educational Purpose:** MedGuide is designed solely for educational understanding of medical language. It does **not** provide medical diagnoses, treatment plans, or prescription recommendations.
- **Safety Advisory:** Always consult a qualified healthcare professional or emergency medical services for health concerns.
