-- Proposed SQLite database schema for future backend integration.
-- Not yet connected to the browser prototype. Never store plaintext passwords.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL,
 display_name TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS savings_goals (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(id),
 name TEXT NOT NULL, target_cents INTEGER NOT NULL CHECK(target_cents > 0),
 saved_cents INTEGER NOT NULL DEFAULT 0 CHECK(saved_cents >= 0)
);
-- Member 4: one row per deposit into a savings goal (deposit history).
-- request_id is optional; when the frontend sends one, the UNIQUE rule stops
-- the same deposit being saved twice (for example after a double-click).
CREATE TABLE IF NOT EXISTS savings_deposits (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 goal_id INTEGER NOT NULL REFERENCES savings_goals(id),
 user_id INTEGER NOT NULL REFERENCES users(id),
 amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
 request_id TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id, request_id)
);
CREATE TABLE IF NOT EXISTS budgets (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(id),
 category TEXT NOT NULL, month TEXT NOT NULL,
 limit_cents INTEGER NOT NULL CHECK(limit_cents >= 0),
 UNIQUE(user_id,category,month)
);
CREATE TABLE IF NOT EXISTS transactions (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(id),
 category TEXT NOT NULL, description TEXT NOT NULL,
 amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
 kind TEXT NOT NULL CHECK(kind IN ('income','expense','saving')),
 occurred_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mascots (
 user_id INTEGER PRIMARY KEY REFERENCES users(id),
 name TEXT NOT NULL DEFAULT 'Sprout', xp INTEGER NOT NULL DEFAULT 0 CHECK(xp >= 0),
 last_checkin TEXT
);
