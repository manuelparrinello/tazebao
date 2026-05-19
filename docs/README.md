# Tazebao — Documentazione Tecnica

ERP gestionale italiano (single-user/small-team). Flask 3.1, SQLAlchemy 2.0, SQLite, Jinja2.

## Indice della documentazione

| Documento | Descrizione |
|-----------|-------------|
| [ARCHITETTURA.md](ARCHITETTURA.md) | Stack tecnologico, factory `create_app()`, blueprint, auth flow, storage |
| [DB.md](DB.md) | Schema DB: tabelle, colonne, enum, relazioni, diagramma ER |
| [ROTTE.md](ROTTE.md) | Route HTML per ogni blueprint (metodo, URL, descrizione, guard) |
| [API.md](API.md) | API REST (`/api/`): endpoint, metodo, body richiesta, risposta |

## Stack

- **Runtime**: Python 3.10+
- **Framework**: Flask 3.1
- **ORM**: SQLAlchemy 2.0 + Flask-SQLAlchemy
- **Migrationi**: Flask-Migrate 4.1 (Alembic, batch mode per SQLite)
- **Form/CSRF**: Flask-WTF 1.2 (CSRFProtect globale; `api.bp` esente)
- **CORS**: Flask-CORS 6.0
- **DB**: SQLite (`app.db`)
- **Template**: Jinja2, Bootstrap 5
- **Email**: IMAP/SMTP via `imaplib`/`smtplib`, password criptate con Fernet
- **Dipendenza legacy**: PyInstaller, PyAutoGUI, PyMuPDF (in `requirements.txt`)

## Setup rapido

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # compilare SECRET_KEY, EMAIL_CREDENTIALS_KEY
flask --app app.py db upgrade
flask --app app.py create-admin --email ... --password "..." --name "..."
python run.py
```

- `SECRET_KEY` obbligatoria in produzione (dev usa `dev-secret-key`)
- `EMAIL_CREDENTIALS_KEY` generata con `Fernet.generate_key()`
- Locale italiana impostata su `it_IT.UTF-8`

## Struttura directory

```
tazebao/
├── app/
│   ├── __init__.py          # create_app, filtri template, alias legacy
│   ├── extensions.py        # db, migrate, cors, csrf
│   ├── auth.py              # login_required, role_required, before_request
│   ├── models.py            # 17 classi modello
│   ├── cli.py               # comando flask create-admin
│   ├── routes/              # 15 blueprint
│   ├── utils/               # parsing, calendar_helpers, ...
│   ├── services/            # finance_service, mail_service, ...
│   └── storage_utils.py     # filesystem lato server
├── templates/               # Jinja2
├── static/                  # CSS, JS, uploads
├── storage/                 # filesystem clienti/lavori
├── migrations/              # Alembic (attive: 0001-0003)
├── docs/                    # ← documentazione corrente
├── run.py / app.py          # entry point
└── .env                     # variabili ambiente
```
