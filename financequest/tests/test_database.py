import unittest
import tempfile
from pathlib import Path
import sqlite3

from flask import Flask
from services.database import get_db

class DatabaseTestCase(unittest.TestCase):

    def setUp(self):
        # Create a temporary database for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["DATABASE"] = str(self.db_path)

        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        # Close the SQLite connection before deleting the test database
        from services.database import close_db

        close_db()
        self.ctx.pop()
        self.temp_dir.cleanup()

    def test_get_db_creates_connection(self):
        """Verify get_db creates a working database connection."""
        db = get_db()

        result = db.execute("SELECT 1").fetchone()

        self.assertEqual(result[0], 1)

    def test_get_db_reuses_connection(self):
        """Verify repeated calls reuse the same database connection."""
        db1 = get_db()
        db2 = get_db()

        self.assertIs(db1, db2)

    def test_close_db_closes_connection(self):
        """Verify close_db closes an existing SQLite connection."""
        from services.database import close_db

        db = get_db()
        close_db()

        # A closed connection should reject SQL queries. 
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute("SELECT 1")

    def test_close_db_without_connection(self):
        """Verify close_db safely handles no active connection."""
        from services.database import close_db

        # No database connection has been opened.
        close_db()

        # Calling close_db again should also be safe.
        close_db()

    def test_init_db_creates_tables(self):
        """Verify init_db creates the database tables."""
        from services.database import init_db

        init_db()
        db = get_db()

        result = db.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()

        self.assertTrue(len(result) > 0)

    def test_get_db_creates_missing_directory(self):
        """Verify get_db creates missing parent directories."""
        nested_path = Path(self.temp_dir.name) / "nested" / "dir" / "test.db"
        self.app.config["DATABASE"] = str(nested_path)

        db = get_db()
        result = db.execute("SELECT 1").fetchone()

        self.assertEqual(result[0], 1)
        self.assertTrue(nested_path.parent.is_dir())

    def test_get_db_invalid_path(self):
        """Verify get_db rejects a directory used as a database file."""
        self.app.config["DATABASE"] = str(self.temp_dir.name)

        with self.assertRaises(sqlite3.OperationalError):
            get_db()

    def test_init_db_called_twice(self):
        """Verify how init_db handles repeated initialization."""
        from services.database import init_db

        init_db()

        # The second initialization should either succeed or raise
        # an error if the schema does not support repeated creation.
        try: 
            init_db()
        except sqlite3.OperationalError as error:
            self.assertIn("already exists", str (error). lower())
        else:
            db = get_db()
            result = db.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()
            self.assertGreater(result[0], 0)

    def test_init_db_missing_schema(self):
        """Verify init_db raises an error when schema.sql is missing."""
        from unittest.mock import patch
        from services.database import init_db
        import services.database as database

        # Redirect the schema lookup to an empty temporary directory. 
        with patch.object(database, "BASE_DIR", Path(self.temp_dir.name)):
            with self.assertRaises(FileNotFoundError):
                init_db()

    def test_close_db_allows_reconnection(self):
        """Verify a new connection can be opened after closing one."""
        from services.database import close_db

        first_db = get_db()
        close_db()

        second_db = get_db()

        self.assertIsNot(first_db, second_db)
        self.assertEqual(
            second_db.execute("SELECT 1").fetchone()[0], 1
        )

if __name__ == "__main__":
    unittest.main()