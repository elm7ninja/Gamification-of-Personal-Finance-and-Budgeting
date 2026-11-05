# Six-member implementation plan

The original UI still runs as a localStorage demo in `static/js/app.js`. **No persistent Flask financial APIs have been implemented yet.** Each team member replaces the designated HTTP 501 placeholders with secure working features and adds tests. The design may be adjusted after group approval.

| Owner | Modules | Definition of done |
|---|---|---|
| Member 1 | `routes/auth.py`, `models/users.py` | Register, log in/out; hash passwords; sessions; unauthorized requests rejected |
| Member 2 | `routes/transactions.py`, `models/transactions.py` | Add/list/edit/delete own entries; validate cents; filtering; tests |
| Member 3 | `routes/budgets.py`, `models/budgets.py` | Category/month budgets; compute spent from transactions; 80/100% alerts; tests |
| Member 4 | `routes/savings.py`, `models/savings.py` | Create goals, add deposits atomically; prevent negative deposits; tests |
| Member 5 | `routes/mascot.py`, `models/mascot.py`, `services/gamification.py` | Deterministic XP/stage rules; no duplicate daily rewards; achievements; tests |
| Member 6 | `routes/dashboard.py`, `static/js/modules/*`, integration tests | API-powered summary; connect frontend via fetch; integration and UX tests |

## GitHub workflow
1. Agree on design, API JSON shapes, rewards rules, and the database schema first.
2. Each student creates a feature branch; submit pull requests for review.
3. Do not edit the same large `static/js/app.js` concurrently; assign the migration to Member 6 and gradually delegate modules.
4. Keep database out of Git (`.gitignore`). Use example data, not actual financial data.
5. Agree on acceptance tests (both success and failure cases) before replacing each 501 placeholder.
6. Integrate often: run `python3 -m unittest discover -s tests -v` after each merge.

## Suggested order
Authentication/database access -> transactions -> savings and budgets -> mascot rules -> dashboard API -> replace localStorage calls -> integration tests.

## Security baseline
Flask development secret is not production-safe. Use environment variables in deployment; hashed passwords, signed-in sessions, user-scoped queries, parameterized SQL, CSRF protection where needed, and never trust a user_id supplied in a request.
