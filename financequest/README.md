# FinanceQuest: team development starter

This is the actual FinanceQuest prototype separated into template, CSS, and JS plus **unfinished Flask API modules**. It deliberately keeps the working demo unchanged so your group can compare it as the backend is built.

## Quick start (macOS / VS Code)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```
Open http://127.0.0.1:5000 in your browser. Stop with Ctrl+C.

## Run tests
```bash
python3 -m unittest discover -s tests -v
```
Tests currently verify that the homepage and health check work and that unfinished endpoints correctly return HTTP 501. **Passing these does not mean finance features are implemented.**

## Where your group codes
- `routes/`: Flask API endpoints (currently intentional TODO/HTTP 501)
- `models/`: SQLite persistence modules to implement
- `services/`: database and gamification helpers
- `static/js/modules/`: frontend code to replace the browser-only demo
- `tests/`: expand with real unit/integration tests
- `schema.sql`: initial database design (not wired to the app)
- `docs/TEAM_TASKS.md`: recommended assignment of six students

The existing `static/js/app.js` runs a browser-localStorage demo; data does not persist on the server and does not belong to authenticated users. Do not claim it is a complete backend.

This starter is for a student development environment, not production deployment.
