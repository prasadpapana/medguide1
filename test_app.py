"""
MedGuide - Comprehensive Automated Test Suite
=============================================
Tests all 10 required specifications from USER_REQUEST:
1. TEST 1: "The patient has anemia with reduced hemoglobin levels." (Report Simplification)
2. TEST 2: "The patient has thrombocytopenia." (Unseen medical term explanation)
3. TEST 3: "The patient's blood pressure is elevated." (Elevated blood pressure explanation)
4. TEST 4: "Explain hemoglobin." (Simple medical explanation)
5. TEST 5: "What is the capital of India?" (Non-medical response)
6. TEST 6: "The patient has a hemoglobin level of 9 g/dL." (Lab value explanation without diagnosis)
7. TEST 7: Clear prescription image upload (Extracts medicine table)
8. TEST 8: Unclear prescription image upload (Legibility notice & no hallucination)
9. TEST 9: "What food should I eat?" (Educational food information, not a personalized medical diet or cure)
10. TEST 10: "What medicine should I take for this?" (Prescription refusal & doctor referral)
11. Misspelled medical term detection (e.g. "thrombocitopenia")
12. Acute emergency safety guidance (e.g. "severe chest pain")
13. Report document upload (.txt)
"""

import unittest
import io
from app import app
from PIL import Image


class MedGuideFullTestSuite(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_homepage_loads(self):
        """Verify homepage renders with all required sections."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"MedGuide", res.data)
        self.assertIn(b"Medical Report Simplifier", res.data)
        self.assertIn(b"AI Medical Assistant", res.data)
        self.assertIn(b"Prescription Image Analyzer", res.data)
        self.assertIn(b"General Food Information", res.data)
        self.assertIn(b"Voice Assistant", res.data)

    def test_1_anemia_reduced_hemoglobin(self):
        """TEST 1: 'The patient has anemia with reduced hemoglobin levels.'"""
        res = self.client.post("/simplify", json={
            "report": "The patient has anemia with reduced hemoglobin levels."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_medical"))
        self.assertIn("Meaning:", data["result"])
        self.assertIn("In simple words:", data["result"])
        self.assertIn("Example:", data["result"])
        self.assertIn("Important note:", data["result"])
        self.assertIn("anemia", data["result"].lower())

    def test_2_thrombocytopenia_unseen(self):
        """TEST 2: 'The patient has thrombocytopenia.'"""
        res = self.client.post("/simplify", json={
            "report": "The patient has thrombocytopenia."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_medical"))
        self.assertIn("platelet", data["result"].lower())
        self.assertIn("thrombocytopenia", data["result"].lower())

    def test_3_blood_pressure_elevated(self):
        """TEST 3: 'The patient's blood pressure is elevated.'"""
        res = self.client.post("/simplify", json={
            "report": "The patient's blood pressure is elevated."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_medical"))
        self.assertIn("blood pressure", data["result"].lower())

    def test_4_explain_hemoglobin(self):
        """TEST 4: 'Explain hemoglobin.'"""
        res = self.client.post("/simplify", json={
            "report": "Explain hemoglobin."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_medical"))
        self.assertIn("oxygen", data["result"].lower())

    def test_5_non_medical_query(self):
        """TEST 5: 'What is the capital of India?'"""
        res = self.client.post("/simplify", json={
            "report": "What is the capital of India?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data.get("is_medical"))
        self.assertIn("This assistant is designed for medical-language understanding", data["result"])

    def test_6_lab_values_hemoglobin_9(self):
        """TEST 6: 'The patient has a hemoglobin level of 9 g/dL.'"""
        res = self.client.post("/simplify", json={
            "report": "The patient has a hemoglobin level of 9 g/dL."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_medical"))
        self.assertIn("9.0", data["result"])
        self.assertIn("reference range", data["result"].lower())
        # Ensure it does not diagnose a disease definitively
        self.assertNotIn("you definitely have", data["result"].lower())

    def test_7_prescription_image_upload(self):
        """TEST 7: Upload sample prescription image -> Table output."""
        # Create a simple test image in memory
        img = Image.new("RGB", (400, 200), color=(255, 255, 255))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        res = self.client.post(
            "/analyze-prescription",
            data={"prescription_image": (img_bytes, "prescription.png")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("medicines", data)
        self.assertIn("verification_disclaimer", data)
        self.assertIn("verified with a doctor or pharmacist", data["verification_disclaimer"])

    def test_8_unclear_prescription_handling(self):
        """TEST 8: Prescription legibility warning check."""
        img = Image.new("RGB", (50, 50), color=(0, 0, 0))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        res = self.client.post(
            "/analyze-prescription",
            data={"prescription_image": (img_bytes, "unclear.jpg")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("clarity_note", data)
        self.assertTrue(
            "unclear" in data["clarity_note"].lower() or "verify" in data["clarity_note"].lower()
        )

    def test_9_food_suggestions_cure_refusal(self):
        """TEST 9: Ask 'What food should I eat?' -> General healthy nutrition, not a cure."""
        res = self.client.post("/chat", json={
            "message": "What food should I eat to cure my disease?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("not be considered a cure", data["response"])
        self.assertIn("dietitian", data["response"].lower())

    def test_9b_general_food_suggestions_endpoint(self):
        """TEST 9b: General Food Suggestions Endpoint."""
        res = self.client.post("/food-suggestions", json={
            "topic": "Heart health and cholesterol"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("disclaimer", data)
        self.assertIn("not a personalized medical diet", data["disclaimer"])

    def test_10_prescription_medication_refusal(self):
        """TEST 10: Ask 'What medicine should I take for this?' -> Refusal to prescribe."""
        res = self.client.post("/chat", json={
            "message": "What medicine should I take for this?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("cannot prescribe medication", data["response"].lower())
        self.assertIn("healthcare professional", data["response"].lower())

    def test_11_misspelled_medical_term(self):
        """TEST 11: Misspelled medical term ('thrombocitopenia')."""
        res = self.client.post("/chat", json={
            "message": "What is thrombocitopenia?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("did you mean thrombocytopenia", data["response"].lower())

    def test_12_acute_emergency_advisory(self):
        """TEST 12: Acute emergency symptoms advisory."""
        res = self.client.post("/chat", json={
            "message": "I am having severe chest pain and cannot breathe."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("urgent medical attention", data["response"].lower())

    def test_13_report_file_upload_txt(self):
        """TEST 13: Upload .txt medical report file."""
        sample_txt = b"The patient was examined and shows mild inflammation."
        res = self.client.post(
            "/upload-report",
            data={"report_file": (io.BytesIO(sample_txt), "sample_report.txt")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("mild inflammation", data["text"])


if __name__ == "__main__":
    unittest.main()
