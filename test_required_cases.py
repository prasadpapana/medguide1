import os
import sys
import unittest
from ai_service import simplify_medical_text, chat_with_gemini, get_food_suggestions

class TestMedGuideAIService(unittest.TestCase):

    def test_01_what_is_migraine_mean(self):
        res = simplify_medical_text("What is migraine mean?")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        self.assertIn("structured", res)
        self.assertTrue(len(res["structured"]["meaning"]) > 10)
        self.assertTrue(len(res["structured"]["in_simple_words"]) > 10)
        print("PASS 1: 'What is migraine mean?'")

    def test_02_what_does_migraine_mean(self):
        res = simplify_medical_text("What does migraine mean?")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        self.assertIn("structured", res)
        print("PASS 2: 'What does migraine mean?'")

    def test_03_explain_migraine(self):
        res = simplify_medical_text("Explain migraine.")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        self.assertIn("structured", res)
        print("PASS 3: 'Explain migraine.'")

    def test_04_what_is_thrombocytopenia(self):
        res = simplify_medical_text("What is thrombocytopenia?")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        self.assertIn("structured", res)
        print("PASS 4: 'What is thrombocytopenia?'")

    def test_05_what_does_elevated_bilirubin_mean(self):
        res = simplify_medical_text("What does elevated bilirubin mean?")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        self.assertIn("structured", res)
        print("PASS 5: 'What does elevated bilirubin mean?'")

    def test_06_ultrasound_gallstone(self):
        res = simplify_medical_text("The ultrasound report describes a small gallstone.")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        self.assertIn("structured", res)
        print("PASS 6: 'The ultrasound report describes a small gallstone.'")

    def test_07_what_is_leukocytosis(self):
        res = simplify_medical_text("What is leukocytosis?")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        self.assertIn("structured", res)
        print("PASS 7: 'What is leukocytosis?'")

    def test_08_explain_microscopic_hematuria(self):
        res = simplify_medical_text("Explain microscopic hematuria.")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        self.assertIn("structured", res)
        print("PASS 8: 'Explain microscopic hematuria.'")

    def test_09_heart_healthy_eating(self):
        res = simplify_medical_text("What food is generally associated with heart-healthy eating?")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["is_medical"])
        print("PASS 9: 'What food is generally associated with heart-healthy eating?'")

    def test_10_java_program_non_medical(self):
        res = simplify_medical_text("How to write a Java program?")
        self.assertEqual(res["status"], "success")
        self.assertFalse(res["is_medical"])
        self.assertEqual(res["type"], "non_medical")
        self.assertIn("designed for medical-language", res["result"])
        print("PASS 10: 'How to write a Java program?' -> Correctly classified as non-medical!")

    def test_11_chat_natural_questions(self):
        chat_res = chat_with_gemini("What does thrombocytopenia mean?")
        self.assertEqual(chat_res["status"], "success")
        self.assertTrue(len(chat_res["response"]) > 20)
        print("PASS 11: Chat with natural question passed!")

if __name__ == "__main__":
    unittest.main()
