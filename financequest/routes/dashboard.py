"""Team implementation placeholder. Replace 501 routes with tested database logic."""
from flask import Blueprint, jsonify
bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

@bp.route("/", methods=["GET"])
def dashboard_0():
    """TODO: Aggregate balance, income, expenses, savings and recent transactions."""
    return jsonify(error="not_implemented", feature="dashboard", task='Aggregate balance, income, expenses, savings and recent transactions.'), 501
