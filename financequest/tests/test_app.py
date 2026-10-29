import unittest
from app import create_app


class FlaskSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    def test_homepage(self):
        result = self.client.get("/")
        self.assertEqual(result.status_code, 200)
        self.assertIn(b"FinanceQuest", result.data)

    def test_health(self):
        result = self.client.get("/api/health")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["status"], "ok")


if __name__ == "__main__":
    unittest.main()
