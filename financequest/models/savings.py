"""SQLite access for savings goals and deposits (Member 4).

Rules followed in this module:
- Every query is parameterized and scoped by user_id, so one user can never
  read or change another user's goals.
- Money is stored as integer cents. Use parse_amount_to_cents() to convert
  dollar amounts from the frontend.
- A deposit is recorded atomically: the deposit row, the goal's new
  saved_cents and the matching 'saving' transaction are written together or
  not at all.
"""
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation

MAX_NAME_LENGTH = 100
MAX_AMOUNT_CENTS = 1_000_000_000  # $10,000,000 - a sanity cap for a student app
MAX_REQUEST_ID_LENGTH = 64


class SavingsValidationError(ValueError):
    """Raised when user input for a goal or deposit is invalid."""


def parse_amount_to_cents(value, field="amount"):
    """Convert a dollar amount (number or numeric string) to integer cents.

    Rejects missing values, booleans, non-numbers, NaN/infinity, more than two
    decimal places, amounts of $0 or less, and amounts above the cap.
    """
    if value is None or isinstance(value, bool):
        raise SavingsValidationError(f"{field} is required and must be a number.")
    if isinstance(value, str):
        value = value.strip()
    try:
        # str() avoids binary float surprises such as Decimal(0.1).
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise SavingsValidationError(f"{field} must be a number.") from None
    if not amount.is_finite():
        raise SavingsValidationError(f"{field} must be a finite number.")
    if amount != amount.quantize(Decimal("0.01")):
        raise SavingsValidationError(f"{field} cannot have more than two decimal places.")
    cents = int(amount * 100)
    if cents <= 0:
        raise SavingsValidationError(f"{field} must be greater than $0.")
    if cents > MAX_AMOUNT_CENTS:
        raise SavingsValidationError(f"{field} is too large.")
    return cents


def clean_goal_name(name):
    """Trim and validate a goal name."""
    if not isinstance(name, str) or not name.strip():
        raise SavingsValidationError("name is required.")
    name = name.strip()
    if len(name) > MAX_NAME_LENGTH:
        raise SavingsValidationError(f"name must be {MAX_NAME_LENGTH} characters or fewer.")
    return name


def clean_request_id(request_id):
    """Validate the optional client-supplied id used to block duplicate deposits."""
    if request_id is None:
        return None
    if not isinstance(request_id, str) or not request_id.strip():
        raise SavingsValidationError("request_id must be a non-empty string.")
    request_id = request_id.strip()
    if len(request_id) > MAX_REQUEST_ID_LENGTH:
        raise SavingsValidationError(
            f"request_id must be {MAX_REQUEST_ID_LENGTH} characters or fewer."
        )
    return request_id


def progress_percent(saved_cents, target_cents):
    """Whole-number percent saved, rounded down and capped at 100.

    Rounding down means a goal only shows 100% once it is actually complete.
    Example: $150 of $500 -> 30.
    """
    if target_cents <= 0:
        return 0
    return min(100, saved_cents * 100 // target_cents)


def goal_to_dict(row):
    """Shape a savings_goals row as the JSON the API returns."""
    target = row["target_cents"]
    saved = row["saved_cents"]
    return {
        "id": row["id"],
        "name": row["name"],
        "target_cents": target,
        "saved_cents": saved,
        "remaining_cents": max(0, target - saved),
        "progress_percent": progress_percent(saved, target),
        "completed": saved >= target,
    }


def deposit_to_dict(row):
    return {
        "id": row["id"],
        "goal_id": row["goal_id"],
        "amount_cents": row["amount_cents"],
        "request_id": row["request_id"],
        "created_at": row["created_at"],
    }


def list_goals(db, user_id):
    """Return the user's goals, oldest first, as dicts."""
    rows = db.execute(
        "SELECT id, name, target_cents, saved_cents FROM savings_goals "
        "WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    return [goal_to_dict(row) for row in rows]


def get_goal(db, user_id, goal_id):
    """Return one goal owned by the user, or None."""
    row = db.execute(
        "SELECT id, name, target_cents, saved_cents FROM savings_goals "
        "WHERE id = ? AND user_id = ?",
        (goal_id, user_id),
    ).fetchone()
    return goal_to_dict(row) if row else None


def savings_summary(db, user_id):
    """Totals across all of a user's goals.

    overall_progress_percent is the average progress of all goals (each capped
    at 100%). This matches the demo's mascot growth rule, so Member 5's
    mascot/gamification code can call this to decide the mascot's stage.
    """
    goals = list_goals(db, user_id)
    total_saved = sum(goal["saved_cents"] for goal in goals)
    total_target = sum(goal["target_cents"] for goal in goals)
    overall = (
        sum(goal["progress_percent"] for goal in goals) // len(goals) if goals else 0
    )
    return {
        "goal_count": len(goals),
        "total_saved_cents": total_saved,
        "total_target_cents": total_target,
        "completed_count": sum(1 for goal in goals if goal["completed"]),
        "overall_progress_percent": overall,
    }


def create_goal(db, user_id, name, target_cents):
    """Insert a new goal for the user and return it."""
    cursor = db.execute(
        "INSERT INTO savings_goals (user_id, name, target_cents) VALUES (?, ?, ?)",
        (user_id, name, target_cents),
    )
    db.commit()
    return get_goal(db, user_id, cursor.lastrowid)


def add_deposit(db, user_id, goal_id, amount_cents, request_id=None):
    """Record a deposit and raise the goal's saved total in one transaction.

    Returns (goal, deposit, duplicate):
    - (None, None, False) if the goal does not exist or is not the user's.
    - duplicate=True if this request_id was already used by this user; nothing
      new is written and the original deposit is returned.
    """
    try:
        # IMMEDIATE takes the write lock up front, so two deposits arriving at
        # the same time cannot both read the old total.
        db.execute("BEGIN IMMEDIATE")

        goal = db.execute(
            "SELECT id, name FROM savings_goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id),
        ).fetchone()
        if goal is None:
            db.rollback()
            return None, None, False

        if request_id is not None:
            existing = db.execute(
                "SELECT id, goal_id, amount_cents, request_id, created_at "
                "FROM savings_deposits WHERE user_id = ? AND request_id = ?",
                (user_id, request_id),
            ).fetchone()
            if existing is not None:
                db.rollback()
                return get_goal(db, user_id, existing["goal_id"]), deposit_to_dict(existing), True

        cursor = db.execute(
            "INSERT INTO savings_deposits (goal_id, user_id, amount_cents, request_id) "
            "VALUES (?, ?, ?, ?)",
            (goal_id, user_id, amount_cents, request_id),
        )
        deposit_id = cursor.lastrowid

        db.execute(
            "UPDATE savings_goals SET saved_cents = saved_cents + ? "
            "WHERE id = ? AND user_id = ?",
            (amount_cents, goal_id, user_id),
        )

        # Log it as a 'saving' transaction (like the demo does) so the
        # transaction history and dashboard can show deposits.
        db.execute(
            "INSERT INTO transactions "
            "(user_id, category, description, amount_cents, kind, occurred_on) "
            "VALUES (?, 'Savings', ?, ?, 'saving', ?)",
            (user_id, f"{goal['name']} deposit", amount_cents, date.today().isoformat()),
        )

        db.commit()
    except sqlite3.Error:
        db.rollback()
        raise

    deposit = db.execute(
        "SELECT id, goal_id, amount_cents, request_id, created_at "
        "FROM savings_deposits WHERE id = ?",
        (deposit_id,),
    ).fetchone()
    return get_goal(db, user_id, goal_id), deposit_to_dict(deposit), False
