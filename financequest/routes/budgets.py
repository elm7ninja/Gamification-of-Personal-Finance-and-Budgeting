"""Team implementation placeholder. Replace 501 routes with tested database logic."""
from flask import Blueprint, jsonify
bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")

@bp.route("/", methods=["GET"])
def budgets_0():
    """TODO: List monthly category budgets and computed spending."""
    return jsonify(error="not_implemented", feature="budgets", task='List monthly category budgets and computed spending.'), 501

@bp.route("/", methods=["POST"])
def budgets_1():
    """TODO: Create/update a budget limit and validate amount."""
    return jsonify(error="not_implemented", feature="budgets", task='Create/update a budget limit and validate amount.'), 501

@bp.route("/alerts", methods=["GET"])
def budgets_2():
    """TODO: Return 80% and 100% threshold alerts."""
    return jsonify(error="not_implemented", feature="budgets", task='Return 80% and 100% threshold alerts.'), 501
