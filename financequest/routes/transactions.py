"""Team implementation placeholder. Replace 501 routes with tested database logic."""
from flask import Blueprint, jsonify
bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")

@bp.route("/", methods=["GET"])
def transactions_0():
    """TODO: List signed-in user's transactions (optional category/date filters)."""
    return jsonify(error="not_implemented", feature="transactions", task="List signed-in user's transactions (optional category/date filters)."), 501

@bp.route("/", methods=["POST"])
def transactions_1():
    """TODO: Create an income/expense transaction in integer cents."""
    return jsonify(error="not_implemented", feature="transactions", task='Create an income/expense transaction in integer cents.'), 501

@bp.route("/<int:item_id>", methods=["PATCH"])
def transactions_2(item_id=None):
    """TODO: Edit an owned transaction."""
    return jsonify(error="not_implemented", feature="transactions", task='Edit an owned transaction.'), 501

@bp.route("/<int:item_id>", methods=["DELETE"])
def transactions_3(item_id=None):
    """TODO: Delete an owned transaction."""
    return jsonify(error="not_implemented", feature="transactions", task='Delete an owned transaction.'), 501
