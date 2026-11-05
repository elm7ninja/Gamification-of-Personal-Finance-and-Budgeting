"""TODO: Extract reusable application logic here. No database writes yet."""
import sqlite3
from pathlib import Path
from flask import current_app, g

#Project directory containing scheme.sql file
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "instance" / "financequest.db"

def get_db():
    """Get a database connection for the current Flask reques. """
    if "db" not in g:
        db_path = Path(
                current_app.config.get("DATABASE", DEFAULT_DB_PATH)     
        )
        db_path.parent.mkdir(parents=True, exist_ok=True)

        g.db = sqlite3.connect(str(db_path))
        g.db.row_factory = sqlite3.Row

        g.db.execute("PRAGMA foreign_keys = ON;")

    return g.db

def close_db(error=None):
    """Close the database connection for the current Flask request."""
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_db():
    """Initialize the database with the schema defined in schema.sql."""
    db = get_db()
    schema_path = BASE_DIR / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        db.executescript(schema_file.read())

    db.commit()  # Commit the changes to the database


def init_app(app):
    """Register the database functions with the Flask application."""
    app.teardown_appcontext(close_db)