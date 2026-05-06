# AGENTS.md

## Project
Flask ERP (Italian-language business management app). SQLite + SQLAlchemy, Flask-Migrate/Alembic, Jinja2 templates. Single-user or small-team internal tool.

## Dev commands

```bash
python -m venv venv && source venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
cp .env.example .env                               # fill SECRET_KEY, EMAIL_CREDENTIALS_KEY, FLASK_ENV
flask --app app.py db upgrade                      # apply migrations
flask --app app.py create-admin --email ... --password "..." --name "..."
python run.py                                      # dev server on :5000
```

- Generate `EMAIL_CREDENTIALS_KEY`: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `SECRET_KEY` is **required in production** — app raises `RuntimeError` if missing and not dev.
- No test suite, linter, formatter, or CI exists. Do not invent them.

## Architecture

- Entry point: `run.py` → `app/__init__.py:create_app()` (also `app.py`, identical).
- `app/routes/` contains 14 blueprints: `auth`, `main`, `clienti`, `lavori`, `preventivi`, `tasks`, `calendar`, `editorial_calendar`, `finance`, `emails`, `mail`, `users`, `admin_export`, `api`.
- `app/models.py` — all SQLAlchemy models (User, Cliente, Lavoro, Preventivo, Task, CalendarEvent, EditorialPublication, FinanceMovement, MailAccount, MailMessage, EmailLog, etc.).
- `app/extensions.py` — shared `db`, `migrate`, `csrf`, `cors` instances.
- `app/auth.py` — login/session guards; `app/cli.py` — `create-admin` CLI command.
- `app_legacy.py` — legacy monolith file, do not modify.
- `migrations/versions/` — active migrations (0001–0003). `migrations/versions_archive/` — old migrations, do not touch.

## Key quirks

- **SQLite** at repo root `app.db` (gitignored).
- **CSRF** enabled globally; `api.bp` is the only exempt blueprint.
- `app/__init__.py` registers **legacy URL aliases** via `add_url_rule` for backward compatibility (`/clienti`, `/lavori`, `/preventivi`, etc.).
- Italian locale set on startup (`it_IT.UTF-8`). Template filters: `euroFormat`, `date_it`, `datetime_it`, `nl2br`, global `erp_badge`.
- Email credentials are encrypted at rest with Fernet using `EMAIL_CREDENTIALS_KEY`.
- `PyInstaller`, `PyAutoGUI`, `PyMuPDF` in deps — app is likely packaged as a Windows desktop binary.

## Conventions

- Italian naming throughout (routes, models, templates, UI). Preserve it.
- Templates at `templates/`, static at `static/`. Flask configured with `../templates` and `../static` relative to `app/`.
- `FLASK_ENV=development` enables dev fallback secret key; any other value requires real `SECRET_KEY`.
