# Architettura

## Stack tecnologico

| Livello | Tecnologia |
|---------|-----------|
| Runtime | Python 3.10+ |
| Web framework | Flask 3.1 |
| ORM | SQLAlchemy 2.0 (Flask-SQLAlchemy) |
| Migrazioni DB | Flask-Migrate 4.1 / Alembic (batch mode) |
| Template engine | Jinja2 (Bootstrap 5) |
| Form / CSRF | Flask-WTF 1.2 (CSRFProtect) |
| CORS | Flask-CORS 6.0 |
| Database | SQLite 3 (`app.db`) |
| Email client | `imaplib` + `smtplib` |
| Criptografia | `cryptography.fernet` (password email) |
| Locale | `it_IT.UTF-8` |

## Factory pattern: `create_app()`

`app/__init__.py:create_app()` è la factory dell'applicazione. Sequenza:

1. `load_dotenv()` — carica `.env`
2. Imposta locale italiana (`it_IT.UTF-8`)
3. Crea `Flask(__name__)` con template/static folder spostati su `../templates`, `../static`
4. Configura SQLite (`app.db`), `MAX_CONTENT_LENGTH`, `MAX_FORM_MEMORY_SIZE`
5. Calcola `ERP_STORAGE_ROOT` (default `storage/`)
6. Registra error handler (413, 404, 500)
7. `configure_environment(app)` — imposta `SECRET_KEY` (dev fallback o errore in prod)
8. Inizializza estensioni: `db`, `cors`, `csrf`, `migrate`
9. Registra filtri template (`euroFormat`, `date_it`, `datetime_it`, `nl2br`) e global (`erp_badge`)
10. Registra CLI (`create-admin`)
11. Importa `models`
12. Registra 15 blueprint + alias legacy endpoint
13. Esenta `api.bp` da CSRF
14. `register_auth_guards(app)` — before_request + context_processor

## Blueprint registrati

Ordine di registrazione in `create_app()`:

| # | Blueprint | Prefix | Ruolo |
|---|-----------|--------|-------|
| 1 | `auth.bp` | — | Login/logout |
| 2 | `main.bp` | — | Home, search, app shell |
| 3 | `clienti.bp` | — | CRUD clienti + file browser |
| 4 | `lavori.bp` | — | CRUD lavori + file browser |
| 5 | `preventivi.bp` | — | Preventivi, righe, conversione in lavoro |
| 6 | `tasks.bp` | — | Task ERP |
| 7 | `calendar.bp` | — | Eventi calendario |
| 8 | `editorial_calendar.bp` | — | Piano editoriale social |
| 9 | `moodboards.bp` | — | Moodboard con immagini |
| 10 | `finance.bp` | — | Movimenti finanziari |
| 11 | `emails.bp` | — | Log comunicazioni (EmailLog) |
| 12 | `mail.bp` | — | Account email, sync IMAP, invio SMTP |
| 13 | `users.bp` | — | Gestione utenti |
| 14 | `admin_export.bp` | — | Export CSV/JSON |
| 15 | `api.bp` | — | API REST JSON (CSRF esente) |

## Legacy endpoint alias

`register_legacy_endpoint_aliases()` in `__init__.py` mappa URL brevi su view function dei blueprint per backward compatibilità. Esempi: `/clienti` → `clienti.clienti`, `/lavori` → `lavori.lavori`, `/api/clienti/getall` → `api.get_clienti`.

## Auth flow

`app/auth.py`:

- **`register_auth_guards(app)`**: registra `before_request` che:
  1. Carica `g.current_user` dalla sessione via `current_user()`
  2. Salta se endpoint in `PUBLIC_ENDPOINTS` (`static`, `login`, `auth.login`)
  3. Se utente non autenticato: API → 401 JSON, HTML → redirect a `/login`
- **`login_required`**: decorator per view, redirect a login se `g.current_user` è None
- **`role_required(*roles)`**: come `login_required` + verifica ruolo; fallisce con 403 JSON o redirect
- **Session**: solo `user_id` in sessione; `session.clear()` su logout
- **Password**: hash Werkzeug (`generate_password_hash` / `check_password_hash`)
- **API Auth**: header di sessione standard (cookie-based); risposte 401/JSON per chiamate `/api/`

### PUBLIC_ENDPOINTS

```python
{"static", "login", "auth.login"}
```

## Storage filesystem

`app/storage_utils.py` — utility per la gestione file lato server:

- **Root**: `ERP_STORAGE_ROOT` (default: `storage/` alla root del progetto)
- **Struttura**: `storage/clienti/{id}_{slug}/`, `storage/lavori/{id}_{slug}/`
- **Slug**: ASCII, lowercase, max 60 caratteri
- **Collision**: suffisso numerato (`_1`, `_2`, …)
- **Path safety**: `safe_path()` previene directory traversal
- **Breadcrumb**: utility per navigazione ricorsiva
- **Operazioni**: upload, download, rename, delete, create subfolder
- **Estensioni consentite**: documenti, immagini, video, audio, archivi, file Adobe/Blender

## Template filters & global

| Nome | Tipo | Descrizione |
|------|------|-------------|
| `euroFormat` | filter | Formatta `float` → `1.234,56` |
| `date_it` | filter | `15 Gennaio 2024` |
| `datetime_it` | filter | `15 Gennaio 2024 14:30` |
| `nl2br` | filter | `\n` → `<br>` |
| `erp_badge(kind, value, text)` | global | Badge Bootstrap colorato per stato/priorità/tipo |

## Moduli di servizio

| Path | Ruolo |
|------|-------|
| `app/finance_service.py` | Logica movimenti finanziari, marginalità, riepilogo mensile |
| `app/mail_service.py` | Sync IMAP, invio SMTP, cifratura/decifratura password |
| `app/utils/parsing.py` | Parsing date, float, ID da form/json |
| `app/utils/calendar_helpers.py` | Costanti mesi, bounds mensili, navigazione |
