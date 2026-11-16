import unittest
from app import create_app

class APIScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    def test_api_stubs_are_explicitly_unimplemented(self):
        # Replace these assertions as endpoints become functional.
        # /api/savings/ is implemented (Member 4); see tests/test_savings.py.
        for path in ["/api/dashboard/", "/api/transactions/", "/api/budgets/",
                     "/api/mascot/"]:
            with self.subTest(path=path):
                result = self.client.get(path)
                self.assertEqual(result.status_code, 501)
                self.assertEqual(result.json["error"], "not_implemented")

if __name__ == "__main__":
    unittest.main()
