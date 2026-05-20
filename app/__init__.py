import locale
import os
from datetime import date as date_cls, datetime as datetime_cls

from flask import Flask, flash, redirect, request, url_for
from dotenv import load_dotenv
from markupsafe import Markup, escape
from werkzeug.exceptions import RequestEntityTooLarge

from .auth import register_auth_guards
from .cli import register_cli
from .extensions import cors, csrf, db, migrate


def configure_environment(app):
    flask_env = os.environ.get("FLASK_ENV", "development").lower()
    flask_debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    is_dev = flask_env in {"development", "dev", "local"} or flask_debug
    secret_key = os.environ.get("SECRET_KEY")

    # In produzione SECRET_KEY e obbligatoria: non usare fallback prevedibili.
    if not secret_key:
        if is_dev:
            secret_key = "dev-secret-key"
        else:
            raise RuntimeError(
                "SECRET_KEY non configurata. Imposta SECRET_KEY nelle variabili ambiente."
            )

    app.config["SECRET_KEY"] = secret_key
    app.config["EMAIL_CREDENTIALS_KEY"] = os.environ.get("EMAIL_CREDENTIALS_KEY")
    app.config["ERP_ENV"] = flask_env


def create_app():
    load_dotenv()
    try:
        locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
    except locale.Error:
        pass  # fallback sulla locale di sistema se it_IT non è installata

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_path = os.path.join(basedir, "app.db")
    app.config["DB_PATH"] = db_path
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    storage_root = os.environ.get("ERP_STORAGE_ROOT", "").strip()
    if not storage_root:
        storage_root = os.path.join(basedir, "storage")
        os.makedirs(storage_root, exist_ok=True)
    app.config["ERP_STORAGE_ROOT"] = os.path.abspath(storage_root)

    upload_max_mb = int(os.environ.get("ERP_MAX_UPLOAD_MB", "512"))
    app.config["MAX_CONTENT_LENGTH"] = upload_max_mb * 1024 * 1024

    form_memory_mb = int(os.environ.get("ERP_MAX_FORM_MEMORY_MB", "5"))
    app.config["MAX_FORM_MEMORY_SIZE"] = form_memory_mb * 1024 * 1024

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(e):
        flash(f"File troppo grande. Il limite è di {upload_max_mb} MB.", "danger")
        return redirect(request.referrer or url_for("main.index"))

    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json":
            return {"error": "Risorsa non trovata"}, 404
        flash("Pagina non trovata.", "warning")
        return redirect(url_for("main.index"))

    @app.errorhandler(500)
    def handle_server_error(e):
        if request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json":
            return {"error": "Errore interno del server"}, 500
        flash("Errore interno del server. Riprova più tardi.", "danger")
        return redirect(url_for("main.index"))

    configure_environment(app)

    db.init_app(app)
    cors.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    register_template_filters(app)
    register_cli(app)

    from . import models  # noqa: F401
    from .routes import admin_export, api, auth, calendar, clienti, editorial_calendar, emails, finance, invoices, lavori, mail, main, moodboards, preventivi, tasks, users

    register_auth_endpoint_aliases(app)
    register_legacy_endpoint_aliases(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(clienti.bp)
    app.register_blueprint(lavori.bp)
    app.register_blueprint(preventivi.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(calendar.bp)
    app.register_blueprint(editorial_calendar.bp)
    app.register_blueprint(moodboards.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(emails.bp)
    app.register_blueprint(mail.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(admin_export.bp)
    app.register_blueprint(invoices.bp)
    app.register_blueprint(api.bp)
    csrf.exempt(api.bp)
    register_auth_guards(app)

    return app


def register_template_filters(app):
    italian_months = {
        1: "Gennaio",
        2: "Febbraio",
        3: "Marzo",
        4: "Aprile",
        5: "Maggio",
        6: "Giugno",
        7: "Luglio",
        8: "Agosto",
        9: "Settembre",
        10: "Ottobre",
        11: "Novembre",
        12: "Dicembre",
    }

    def _parse_display_datetime(value):
        if value in (None, ""):
            return None
        if isinstance(value, datetime_cls):
            return value
        if isinstance(value, date_cls):
            return datetime_cls.combine(value, datetime_cls.min.time())
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return None
            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"
            try:
                parsed = datetime_cls.fromisoformat(normalized)
            except ValueError:
                return None
            return parsed
        return None

    def _format_display_date(value, include_time=False):
        parsed = _parse_display_datetime(value)
        if parsed is None:
            return "-"

        day = parsed.day
        month = italian_months.get(parsed.month, "")
        year = parsed.year
        if include_time:
            return f"{day} {month} {year} {parsed:%H:%M}"
        return f"{day} {month} {year}"

    @app.template_filter()
    def euroFormat(value):
        value = float(value)
        return "{:.2f}".format(value).replace(".", ",")

    @app.template_filter("date_it")
    def date_it_filter(value):
        return _format_display_date(value, include_time=False)

    @app.template_filter("datetime_it")
    def datetime_it_filter(value):
        return _format_display_date(value, include_time=True)

    @app.template_filter("nl2br")
    def nl2br_filter(text):
        if text:
            return text.replace("\n", "<br>\n")
        return ""

    def _normalize_badge_key(value):
        if value is None:
            return ""
        return str(value).strip().lower().replace(" ", "_")

    def _titleize(value):
        if value in (None, ""):
            return "-"
        return str(value).replace("_", " ").replace("-", " ").title()

    @app.template_filter("labelize")
    def labelize_filter(value):
        return _titleize(value)

    def _badge_payload(kind, value):
        key = _normalize_badge_key(value)
        mapping = {
            "work_status": {
                "completato": ("success", "Completato"),
                "completata": ("success", "Completato"),
                "in_corso": ("primary", "In corso"),
                "in_attesa": ("warning", "In attesa"),
                "da_iniziare": ("secondary", "Da iniziare"),
                "annullata": ("secondary", "Annullata"),
            },
            "work_priority": {
                "urgente": ("danger", "Urgente"),
                "alta": ("danger", "Alta"),
                "media": ("warning", "Media"),
                "bassa": ("success", "Bassa"),
            },
            "task_status": {
                "da_fare": ("primary", "Da fare"),
                "in_corso": ("primary", "In corso"),
                "in_revisione": ("warning", "In revisione"),
                "completata": ("success", "Completata"),
                "annullata": ("secondary", "Annullata"),
            },
            "task_priority": {
                "urgente": ("danger", "Urgente"),
                "alta": ("danger", "Alta"),
                "media": ("warning", "Media"),
                "bassa": ("success", "Bassa"),
            },
            "task_category": {
                "social_media": ("text-bg-light border", "Social media"),
                "grafica": ("text-bg-light border", "Grafica"),
                "amministrazione": ("text-bg-light border", "Amministrazione"),
                "fotografia": ("text-bg-light border", "Fotografia"),
                "web": ("text-bg-light border", "Web"),
                "commerciale": ("text-bg-light border", "Commerciale"),
                "generale": ("text-bg-light border", "Generale"),
            },
            "quote_status": {
                "bozza": ("warning", "Bozza"),
                "draft": ("warning", "Bozza"),
                "inviato": ("primary", "Inviato"),
                "inviata": ("primary", "Inviato"),
                "in_attesa": ("info", "In attesa"),
                "accettato": ("success", "Accettato"),
                "accettata": ("success", "Accettato"),
                "approvato": ("success", "Accettato"),
                "approvata": ("success", "Accettato"),
                "rifiutato": ("danger", "Rifiutato"),
                "rifiutata": ("danger", "Rifiutato"),
                "scaduto": ("secondary", "Scaduto"),
                "scaduta": ("secondary", "Scaduto"),
                "annullato": ("secondary", "Annullato"),
                "annullata": ("secondary", "Annullato"),
            },
            "event_type": {
                "appuntamento": ("primary", "Appuntamento"),
                "scadenza": ("warning", "Scadenza"),
                "impegno_cliente": ("info", "Impegno cliente"),
                "promemoria": ("secondary", "Promemoria"),
                "generale": ("text-bg-light border", "Generale"),
                "task_due_date": ("warning", "Task"),
            },
            "editorial_status": {
                "idea": ("text-bg-light border", "Idea"),
                "da_produrre": ("primary", "Da produrre"),
                "in_revisione": ("warning", "In revisione"),
                "approvato": ("success", "Approvato"),
                "programmato": ("info", "Programmato"),
                "pubblicato": ("success", "Pubblicato"),
                "annullato": ("secondary", "Annullato"),
            },
            "editorial_platform": {
                "instagram": ("text-bg-light border", "Instagram"),
                "facebook": ("text-bg-light border", "Facebook"),
            },
            "editorial_content_type": {
                "post_grafico": ("text-bg-light border", "Post grafico"),
                "post_fotografico": ("text-bg-light border", "Post fotografico"),
                "storia": ("text-bg-light border", "Storia"),
                "carousel": ("text-bg-light border", "Carousel"),
                "reel": ("text-bg-light border", "Reel"),
                "video": ("text-bg-light border", "Video"),
            },
            "editorial_client_approval": {
                "da_approvare": ("warning", "Da approvare"),
                "approvato": ("success", "Approvato"),
                "modifiche_richieste": ("danger", "Modifiche richieste"),
            },
            "finance_income_status": {
                "effettiva": ("success", "Effettiva"),
                "prevista": ("warning", "Prevista"),
            },
            "finance_expense_type": {
                "fissa": ("secondary", "Fissa"),
                "variabile": ("warning", "Variabile"),
            },
            "finance_category": {
                "pagamento_cliente": ("text-bg-light border", "Pagamento cliente"),
                "fornitore": ("text-bg-light border", "Fornitore"),
                "software": ("text-bg-light border", "Software"),
                "advertising": ("text-bg-light border", "Advertising"),
                "consulenza": ("text-bg-light border", "Consulenza"),
                "attrezzatura": ("text-bg-light border", "Attrezzatura"),
                "tasse": ("text-bg-light border", "Tasse"),
                "stipendio": ("text-bg-light border", "Stipendio"),
                "commercialista": ("text-bg-light border", "Commercialista"),
                "banca": ("text-bg-light border", "Banca"),
                "costituzione_societa": ("text-bg-light border", "Costituzione società"),
                "generale": ("text-bg-light border", "Generale"),
            },
            "finance_movement_type": {
                "entrata": ("success", "Entrata"),
                "uscita": ("danger", "Uscita"),
            },
            "mail_read_status": {
                "read": ("success", "Letta"),
                "unread": ("warning", "Non letta"),
                "inviata": ("primary", "Inviata"),
            },
            "mail_direction": {
                "inbound": ("info", "Ricevuta"),
                "outbound": ("success", "Inviata"),
            },
            "user_role": {
                "admin": ("primary", "Admin"),
                "operatore": ("primary", "Operatore"),
                "readonly": ("secondary", "Readonly"),
            },
            "user_state": {
                "active": ("success", "Attivo"),
                "inactive": ("secondary", "Non attivo"),
            },
        }
        return mapping.get(kind, {}).get(key)

    @app.template_global("erp_badge")
    def erp_badge(kind, value=None, text=None):
        payload = _badge_payload(kind, value)
        if payload:
            variant, default_text = payload
        else:
            variant, default_text = "text-bg-light border", _titleize(value)

        label = text or default_text
        classes = ["badge", "rounded-pill", "erp-badge"]
        if variant:
            normalized_variants = {
                "primary": "text-bg-primary",
                "success": "text-bg-success",
                "warning": "text-bg-warning",
                "danger": "text-bg-danger",
                "info": "text-bg-info",
                "secondary": "text-bg-secondary",
            }
            classes.extend(normalized_variants.get(str(variant), str(variant)).split())
        return Markup(f'<span class="{" ".join(classes)}">{escape(label)}</span>')


def register_auth_endpoint_aliases(app):
    from .routes import auth

    app.add_url_rule(
        "/login",
        endpoint="login",
        view_func=auth.login,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/logout",
        endpoint="logout",
        view_func=auth.logout,
        methods=["POST"],
    )


def register_legacy_endpoint_aliases(app):
    from .routes import api, clienti, lavori, main, preventivi

    aliases = [
        ("index", main.index, "/", ["GET"]),
        ("test", main.test, "/test", ["GET"]),
        ("nuovo_cliente", clienti.nuovo_cliente, "/clienti/new", ["GET", "POST"]),
        ("clienti", clienti.clienti, "/clienti", ["GET"]),
        ("cliente_page", clienti.cliente_page, "/clienti/<int:cliente_id>", ["GET"]),
        ("cliente_delete", clienti.cliente_delete, "/clienti/<int:cliente_id>", ["DELETE"]),
        (
            "cliente_edit",
            clienti.cliente_edit,
            "/clienti/edit/<int:cliente_id>",
            ["GET", "PUT"],
        ),
        ("nuovo_lavoro", lavori.nuovo_lavoro, "/lavori/new", ["GET", "POST"]),
        ("lavori", lavori.lavori, "/lavori", ["GET"]),
        ("lavoro_page", lavori.lavoro_page, "/lavori/<int:lavoro_id>", ["GET"]),
        ("lavoro_delete", lavori.lavoro_delete, "/lavori/<int:lavoro_id>", ["DELETE"]),
        (
            "status_lavoro_update",
            lavori.status_lavoro_update,
            "/lavori/<int:lavoro_id>",
            ["PATCH"],
        ),
        (
            "nuovo_preventivo",
            preventivi.nuovo_preventivo,
            "/preventivi/nuovo",
            ["GET", "POST"],
        ),
        ("preventivi", preventivi.preventivi, "/preventivi", ["GET"]),
        ("render_row", preventivi.render_row, "/presentivi/addrow", ["GET"]),
        (
            "visualizza_preventivo",
            preventivi.visualizza_preventivo,
            "/preventivi/visualizza/<int:id>",
            ["GET"],
        ),
        ("get_clienti", api.get_clienti, "/api/clienti/getall", ["GET"]),
        ("get_lavori", api.get_lavori, "/api/lavori/getall", ["GET"]),
        ("get_lavoro_byID", api.get_lavoro_byID, "/api/lavori/get/<int:id>", ["GET"]),
        (
            "get_cliente_byID",
            api.get_cliente_byID,
            "/api/clienti/get/<int:cliente_id>",
            ["GET"],
        ),
        ("get_ID_by_name", api.get_ID_by_name, "/api/clienti/getid/<string:nome>", ["GET"]),
        ("get_preventivi", api.get_preventivi, "/api/preventivi/getall", ["GET"]),
        (
            "get_preventivo_byID",
            api.get_preventivo_byID,
            "/api/preventivi/get/<int:id>",
            ["GET"],
        ),
    ]

    for legacy_endpoint, view_func, rule, methods in aliases:
        app.add_url_rule(
            rule,
            endpoint=legacy_endpoint,
            view_func=view_func,
            methods=methods,
        )
