"""Tests for Member 4: savings goals and deposits."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import create_app
from models import savings as savings_model
from services.database import get_db


class SavingsTestCase(unittest.TestCase):
    """Each test gets its own temporary database with two example users."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.app = create_app({"TESTING": True, "DATABASE": str(db_path)})
        self.client = self.app.test_client()

        with self.app.app_context():
            db = get_db()
            db.executemany(
                "INSERT INTO users (id, email, password_hash, display_name) VALUES (?, ?, ?, ?)",
                [
                    (1, "alex@example.com", "not-a-real-hash", "Alex"),
                    (2, "sam@example.com", "not-a-real-hash", "Sam"),
                ],
            )
            db.commit()

    def tearDown(self):
        self.temp_dir.cleanup()

    # --- helpers -----------------------------------------------------------

    def login(self, user_id):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id

    def logout(self):
        with self.client.session_transaction() as sess:
            sess.clear()

    def create(self, name="Emergency Fund", target=500):
        return self.client.post("/api/savings/", json={"name": name, "target": target})

    def deposit(self, goal_id, amount, **extra):
        return self.client.post(
            f"/api/savings/{goal_id}/deposit", json={"amount": amount, **extra}
        )

    def query(self, sql, params=()):
        with self.app.app_context():
            return get_db().execute(sql, params).fetchall()


class ListGoalsTests(SavingsTestCase):
    def test_requires_login(self):
        result = self.client.get("/api/savings/")
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.json["error"], "unauthorized")

    def test_user_with_no_goals_gets_empty_list(self):
        self.login(1)
        result = self.client.get("/api/savings/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["goals"], [])
        self.assertEqual(result.json["summary"]["goal_count"], 0)
        self.assertEqual(result.json["summary"]["overall_progress_percent"], 0)

    def test_lists_goals_with_progress(self):
        self.login(1)
        goal_id = self.create("Emergency Fund", 500).json["goal"]["id"]
        self.deposit(goal_id, 150)

        result = self.client.get("/api/savings/")
        self.assertEqual(result.status_code, 200)
        goal = result.json["goals"][0]
        self.assertEqual(goal["target_cents"], 50000)
        self.assertEqual(goal["saved_cents"], 15000)
        self.assertEqual(goal["remaining_cents"], 35000)
        self.assertEqual(goal["progress_percent"], 30)
        self.assertFalse(goal["completed"])

    def test_only_shows_own_goals(self):
        self.login(1)
        self.create("Alex goal", 100)
        self.login(2)
        self.create("Sam goal", 100)

        result = self.client.get("/api/savings/")
        names = [goal["name"] for goal in result.json["goals"]]
        self.assertEqual(names, ["Sam goal"])

    def test_summary_averages_progress(self):
        self.login(1)
        first = self.create("A", 100).json["goal"]["id"]
        self.create("B", 100)
        self.deposit(first, 100)  # 100% and 0% -> 50% average

        summary = self.client.get("/api/savings/").json["summary"]
        self.assertEqual(summary["goal_count"], 2)
        self.assertEqual(summary["completed_count"], 1)
        self.assertEqual(summary["total_saved_cents"], 10000)
        self.assertEqual(summary["overall_progress_percent"], 50)


class CreateGoalTests(SavingsTestCase):
    def test_requires_login(self):
        result = self.create()
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.query("SELECT * FROM savings_goals"), [])

    def test_creates_goal(self):
        self.login(1)
        result = self.create("  New Laptop  ", "1200.50")
        self.assertEqual(result.status_code, 201)
        goal = result.json["goal"]
        self.assertEqual(goal["name"], "New Laptop")  # whitespace trimmed
        self.assertEqual(goal["target_cents"], 120050)
        self.assertEqual(goal["saved_cents"], 0)
        self.assertEqual(goal["progress_percent"], 0)

        rows = self.query("SELECT user_id FROM savings_goals WHERE id = ?", (goal["id"],))
        self.assertEqual(rows[0]["user_id"], 1)

    def test_ignores_user_id_in_body(self):
        self.login(1)
        result = self.client.post(
            "/api/savings/", json={"name": "Sneaky", "target": 10, "user_id": 2}
        )
        self.assertEqual(result.status_code, 201)
        rows = self.query("SELECT user_id FROM savings_goals")
        self.assertEqual(rows[0]["user_id"], 1)

    def test_rejects_invalid_input(self):
        self.login(1)
        cases = {
            "empty name": {"name": "", "target": 100},
            "blank name": {"name": "   ", "target": 100},
            "missing name": {"target": 100},
            "name not text": {"name": 42, "target": 100},
            "name too long": {"name": "x" * 101, "target": 100},
            "zero target": {"name": "Goal", "target": 0},
            "negative target": {"name": "Goal", "target": -5},
            "missing target": {"name": "Goal"},
            "text target": {"name": "Goal", "target": "lots"},
            "boolean target": {"name": "Goal", "target": True},
            "three decimals": {"name": "Goal", "target": 10.005},
            "too large": {"name": "Goal", "target": 10_000_001},
        }
        for label, body in cases.items():
            with self.subTest(label):
                result = self.client.post("/api/savings/", json=body)
                self.assertEqual(result.status_code, 400)
                self.assertEqual(result.json["error"], "validation_error")
        self.assertEqual(self.query("SELECT * FROM savings_goals"), [])

    def test_rejects_non_json_body(self):
        self.login(1)
        result = self.client.post("/api/savings/", data="name=Goal", content_type="text/plain")
        self.assertEqual(result.status_code, 400)
        result = self.client.post("/api/savings/", json=["Goal", 100])
        self.assertEqual(result.status_code, 400)

    def test_session_for_deleted_user_is_rejected(self):
        self.login(999)
        result = self.create()
        self.assertEqual(result.status_code, 401)


class DepositTests(SavingsTestCase):
    def setUp(self):
        super().setUp()
        self.login(1)
        self.goal_id = self.create("Emergency Fund", 500).json["goal"]["id"]

    def test_requires_login(self):
        self.logout()
        result = self.deposit(self.goal_id, 50)
        self.assertEqual(result.status_code, 401)

    def test_deposit_updates_total_and_progress(self):
        self.deposit(self.goal_id, 100)
        result = self.deposit(self.goal_id, 50)

        self.assertEqual(result.status_code, 201)
        self.assertFalse(result.json["duplicate"])
        self.assertEqual(result.json["deposit"]["amount_cents"], 5000)
        goal = result.json["goal"]
        self.assertEqual(goal["saved_cents"], 15000)
        self.assertEqual(goal["progress_percent"], 30)
        self.assertEqual(result.json["summary"]["overall_progress_percent"], 30)

    def test_deposit_is_saved_in_history_and_transactions(self):
        self.deposit(self.goal_id, 25.75)

        deposits = self.query("SELECT goal_id, user_id, amount_cents FROM savings_deposits")
        self.assertEqual([tuple(row) for row in deposits], [(self.goal_id, 1, 2575)])

        tx = self.query("SELECT user_id, kind, amount_cents, description FROM transactions")
        self.assertEqual(
            [tuple(row) for row in tx], [(1, "saving", 2575, "Emergency Fund deposit")]
        )

    def test_rejects_zero_negative_and_invalid_amounts(self):
        for amount in [0, -10, "-0.01", "abc", None, True, 1.001, "NaN", "Infinity"]:
            with self.subTest(amount=amount):
                result = self.deposit(self.goal_id, amount)
                self.assertEqual(result.status_code, 400)
        rows = self.query("SELECT saved_cents FROM savings_goals WHERE id = ?", (self.goal_id,))
        self.assertEqual(rows[0]["saved_cents"], 0)
        self.assertEqual(self.query("SELECT * FROM savings_deposits"), [])

    def test_cannot_deposit_into_someone_elses_goal(self):
        self.login(2)
        result = self.deposit(self.goal_id, 50)
        self.assertEqual(result.status_code, 404)
        rows = self.query("SELECT saved_cents FROM savings_goals WHERE id = ?", (self.goal_id,))
        self.assertEqual(rows[0]["saved_cents"], 0)

    def test_missing_goal_returns_404(self):
        result = self.deposit(9999, 50)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.json["error"], "not_found")

    def test_duplicate_request_id_is_only_counted_once(self):
        first = self.deposit(self.goal_id, 50, request_id="click-123")
        second = self.deposit(self.goal_id, 50, request_id="click-123")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json["duplicate"])
        self.assertEqual(second.json["deposit"]["id"], first.json["deposit"]["id"])
        self.assertEqual(second.json["goal"]["saved_cents"], 5000)
        self.assertEqual(len(self.query("SELECT * FROM savings_deposits")), 1)
        self.assertEqual(len(self.query("SELECT * FROM transactions")), 1)

    def test_different_request_ids_both_count(self):
        self.deposit(self.goal_id, 50, request_id="a")
        result = self.deposit(self.goal_id, 50, request_id="b")
        self.assertEqual(result.json["goal"]["saved_cents"], 10000)

    def test_rejects_bad_request_id(self):
        for request_id in ["", "   ", 123, "x" * 65]:
            with self.subTest(request_id=request_id):
                result = self.deposit(self.goal_id, 50, request_id=request_id)
                self.assertEqual(result.status_code, 400)

    def test_overfunding_caps_progress_at_100(self):
        result = self.deposit(self.goal_id, 600)
        goal = result.json["goal"]
        self.assertEqual(goal["saved_cents"], 60000)
        self.assertEqual(goal["progress_percent"], 100)
        self.assertEqual(goal["remaining_cents"], 0)
        self.assertTrue(goal["completed"])

    def test_failed_write_rolls_back_everything(self):
        """If any part of the deposit fails, nothing is saved (atomic)."""
        with self.app.app_context():
            db = get_db()
            # Make the transaction-log insert fail partway through the deposit.
            db.execute(
                "CREATE TRIGGER fail_tx BEFORE INSERT ON transactions "
                "BEGIN SELECT RAISE(ABORT, 'forced failure'); END"
            )
            db.commit()
            with self.assertRaises(sqlite3.IntegrityError):
                savings_model.add_deposit(db, 1, self.goal_id, 5000)

        rows = self.query("SELECT saved_cents FROM savings_goals WHERE id = ?", (self.goal_id,))
        self.assertEqual(rows[0]["saved_cents"], 0)
        self.assertEqual(self.query("SELECT * FROM savings_deposits"), [])


class ParseAmountTests(unittest.TestCase):
    def test_converts_dollars_to_cents(self):
        self.assertEqual(savings_model.parse_amount_to_cents(50), 5000)
        self.assertEqual(savings_model.parse_amount_to_cents(0.1), 10)
        self.assertEqual(savings_model.parse_amount_to_cents("19.99"), 1999)
        self.assertEqual(savings_model.parse_amount_to_cents(" 7.5 "), 750)

    def test_progress_rounds_down(self):
        self.assertEqual(savings_model.progress_percent(15000, 50000), 30)
        self.assertEqual(savings_model.progress_percent(49999, 50000), 99)
        self.assertEqual(savings_model.progress_percent(50000, 50000), 100)


if __name__ == "__main__":
    unittest.main()
