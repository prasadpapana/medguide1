import io
import json
import unittest
from app import app

class TestAppEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_home_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"MedGuide", res.data)
        print("PASS: Home page renders correctly")

    def test_02_simplify_migraine(self):
        res = self.client.post('/simplify', json={"report": "What is migraine mean?"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["is_medical"])
        self.assertIn("structured", data)
        self.assertIn("meaning", data["structured"])
        print("PASS: /simplify handles natural questions like 'What is migraine mean?'")

    def test_03_simplify_non_medical(self):
        res = self.client.post('/simplify', json={"report": "How to write a Java program?"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertFalse(data["is_medical"])
        self.assertEqual(data["type"], "non_medical")
        print("PASS: /simplify non-medical query handled")

    def test_04_chat_medical(self):
        res = self.client.post('/chat', json={"message": "What does thrombocytopenia mean?", "history": []})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(len(data["response"]) > 20)
        print("PASS: /chat medical question handled")

    def test_05_food_suggestions(self):
        res = self.client.post('/food-suggestions', json={"topic": "Heart health and cholesterol"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("content", data)
        print("PASS: /food-suggestions handled")

    def test_06_upload_report_txt(self):
        file_content = b"Patient has mild anemia and elevated creatinine."
        data = {
            'report_file': (io.BytesIO(file_content), 'test_report.txt')
        }
        res = self.client.post('/upload-report', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        resp = res.get_json()
        self.assertEqual(resp["status"], "success")
        self.assertEqual(resp["text"], "Patient has mild anemia and elevated creatinine.")
        print("PASS: /upload-report TXT upload handled")

if __name__ == '__main__':
    unittest.main()
