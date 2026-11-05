"""FinanceQuest team starter. Frontend demo is preserved; APIs are intentional TODOs."""

from flask import Flask, jsonify, render_template
from routes import auth, transactions, budgets, savings, mascot, dashboard
from services import database


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev-only-change-before-production"
    )

    if test_config:
        app.config.update(test_config)

    # Register SQLite database connection management.
    database.init_app(app)

    # Create database tables if they do not already exist.
    with app.app_context():
        database.init_db()

    # Register the feature blueprints.
    for module in (auth, transactions, budgets, savings, mascot, dashboard):
        app.register_blueprint(module.bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", app="FinanceQuest")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
