"""Team implementation placeholder. Replace 501 routes with tested database logic."""
from flask import Blueprint, jsonify
bp = Blueprint("savings", __name__, url_prefix="/api/savings")

@bp.route("/", methods=["GET"])
def savings_0():
    """TODO: List user's savings goals and percentages."""
    return jsonify(error="not_implemented", feature="savings", task="List user's savings goals and percentages."), 501

@bp.route("/", methods=["POST"])
def savings_1():
    """TODO: Create a new savings goal."""
    return jsonify(error="not_implemented", feature="savings", task='Create a new savings goal.'), 501

@bp.route("/<int:item_id>/deposit", methods=["POST"])
def savings_2(item_id=None):
    """TODO: Record a deposit and atomically update saved_cents."""
    return jsonify(error="not_implemented", feature="savings", task='Record a deposit and atomically update saved_cents.'), 501
