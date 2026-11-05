"""Dashboard API for FinanceQuest."""

from flask import Blueprint, jsonify, request
from services.database import get_db

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.route("/", methods=["GET"])
def dashboard():
    """Return financial summary data for a user."""

    user_id = request.args.get("user_id", type=int)

    if user_id is None or user_id <= 0:
        return jsonify(error="Valid user_id is required"), 400

    db = get_db()

    user = db.execute(
        "SELECT id FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if user is None:
        return jsonify(error="User not found"), 404

    totals = db.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN kind = 'income'
                THEN amount_cents ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN kind = 'expense'
                THEN amount_cents ELSE 0 END), 0) AS expenses
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    savings = db.execute(
        """
        SELECT
            COALESCE(SUM(saved_cents), 0) AS saved,
            COALESCE(SUM(target_cents), 0) AS target
        FROM savings_goals
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    recent = db.execute(
        """
        SELECT id, category, description, amount_cents,
               kind, occurred_on
        FROM transactions
        WHERE user_id = ?
        ORDER BY occurred_on DESC, id DESC
        LIMIT 5
        """,
        (user_id,)
    ).fetchall()

    income = totals["income"]
    expenses = totals["expenses"]

    return jsonify(
        user_id=user_id,
        balance_cents=income - expenses,
        income_cents=income,
        expense_cents=expenses,
        savings_cents=savings["saved"],
        savings_target_cents=savings["target"],
        recent_transactions=[dict(row) for row in recent]
    ), 200
