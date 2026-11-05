"""Team implementation placeholder. Replace 501 routes with tested database logic."""
from flask import Blueprint, jsonify
bp = Blueprint("savings", __name__, url_prefix="/api/savings")

@bp.route("/", methods=["GET"])
def savings_0():
    """
    MEMBER 4 - VIEW SAVINGS GOALS

    TODO:
    1. Connect to the SQLite database.
    2. Retriebe savings goals belonging to the logged-in user.
    3. Calculate the percentage saved for each goal. 
    4. Return the results as JSON.
    5. Handle users who have no savings goals.
    6. Write tests for successful and unsuccessful requests.

    Example: 
    Goal: $500
    Saved: $150
    Progress: 30%
    """
    return jsonify(error="not_implemented", feature="savings", task="List user's savings goals and percentages."), 501

@bp.route("/", methods=["POST"])
def savings_1():
    """ 
MEMBER 4 - CREATE SAVINGS GOAL

TODO:
1. Receive a goal name and target amount from the frontend.
2. Validate empty names and targets of $0 or less.
3. Reject empty names and targets for the logged-in user.
4. Save the goal to SQLite for the logged-in user.
5. Return the newly created goal as JSON.
6. Write tests for valid and invalid inputs.
    """
    return jsonify(error="not_implemented", feature="savings", task='Create a new savings goal.'), 501

@bp.route("/<int:item_id>/deposit", methods=["POST"])
def savings_2(item_id=None):
    """
    MEMBER 4 - ADD MONEY TO SAVINGS

    TODO:
    1. Receive a deposit amount from the frontend.
    2. Verify the savings goal belongs to the logged-in user.
    3. Reject deposits of $0 or less.
    4. Save the deposit and update the total saved in SQLite.
    5. Recalculate savings progress.
    6. Make the updated progress available to the mascot system.
    7. Write tests to prevent duplicate or invalid deposits.

    Example:
    Target: $500
    Previous Saved: $100
    Deposit: $50
    New total: $150
    New progress: 30%
    """
    return jsonify(error="not_implemented", feature="savings", task='Record a deposit and atomically update saved_cents.'), 501
