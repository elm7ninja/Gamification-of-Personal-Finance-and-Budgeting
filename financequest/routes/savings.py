"""Savings goals and deposits API (Member 4).

All amounts in JSON responses are integer cents. Request bodies send dollar
amounts (like the demo UI), e.g. {"name": "Laptop", "target": 1200} or
{"amount": 50.25}.

Endpoints:
    GET  /api/savings/                  -> 200 list of the user's goals + summary
    POST /api/savings/                  -> 201 newly created goal
    POST /api/savings/<id>/deposit      -> 201 deposit + updated goal
                                           (200 if request_id was already used)

Errors: 400 validation_error, 401 unauthorized, 404 not_found.
"""
import sqlite3

from flask import Blueprint, jsonify, request, session

from models import savings as savings_model
from models.savings import SavingsValidationError
from services.database import get_db

bp = Blueprint("savings", __name__, url_prefix="/api/savings")


def current_user_id():
    """Return the signed-in user's id from the session, or None.

    Member 1's login route should put the user's id in session["user_id"].
    The id is never taken from the request body or URL.
    """
    user_id = session.get("user_id")
    return user_id if isinstance(user_id, int) else None


def unauthorized():
    return jsonify(error="unauthorized", message="You must be logged in."), 401


def validation_error(message):
    return jsonify(error="validation_error", message=message), 400


def json_body():
    """Return the JSON object in the request body, or None if it is missing/not an object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@bp.route("/", methods=["GET"])
def list_goals():
    """List the signed-in user's savings goals with progress percentages."""
    user_id = current_user_id()
    if user_id is None:
        return unauthorized()

    db = get_db()
    goals = savings_model.list_goals(db, user_id)
    return jsonify(goals=goals, summary=savings_model.savings_summary(db, user_id)), 200


@bp.route("/", methods=["POST"])
def create_goal():
    """Create a savings goal from {"name": str, "target": dollars}."""
    user_id = current_user_id()
    if user_id is None:
        return unauthorized()

    data = json_body()
    if data is None:
        return validation_error("Request body must be a JSON object.")

    try:
        name = savings_model.clean_goal_name(data.get("name"))
        target_cents = savings_model.parse_amount_to_cents(data.get("target"), field="target")
    except SavingsValidationError as error:
        return validation_error(str(error))

    try:
        goal = savings_model.create_goal(get_db(), user_id, name, target_cents)
    except sqlite3.IntegrityError:
        # The session points at a user that no longer exists.
        return unauthorized()
    return jsonify(goal=goal), 201


@bp.route("/<int:item_id>/deposit", methods=["POST"])
def deposit(item_id):
    """Add {"amount": dollars, "request_id": optional str} to one of the user's goals."""
    user_id = current_user_id()
    if user_id is None:
        return unauthorized()

    data = json_body()
    if data is None:
        return validation_error("Request body must be a JSON object.")

    try:
        amount_cents = savings_model.parse_amount_to_cents(data.get("amount"))
        request_id = savings_model.clean_request_id(data.get("request_id"))
    except SavingsValidationError as error:
        return validation_error(str(error))

    db = get_db()
    goal, deposit_row, duplicate = savings_model.add_deposit(
        db, user_id, item_id, amount_cents, request_id
    )
    if goal is None:
        # Same answer for "doesn't exist" and "belongs to someone else",
        # so users can't probe for other people's goal ids.
        return jsonify(error="not_found", message="Savings goal not found."), 404

    body = {
        "goal": goal,
        "deposit": deposit_row,
        "duplicate": duplicate,
        # For Member 5: overall progress drives the mascot's growth stage.
        "summary": savings_model.savings_summary(db, user_id),
    }
    return jsonify(body), (200 if duplicate else 201)
