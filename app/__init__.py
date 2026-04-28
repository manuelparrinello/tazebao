import locale
import os
import sys

from flask import Flask

from .auth import register_auth_guards
from .cli import register_cli
from .extensions import cors, db, migrate


def create_app():
    locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")

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
    # In produzione impostare SECRET_KEY da variabile d'ambiente.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    db.init_app(app)
    cors.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    register_template_filters(app)
    register_cli(app)

    from . import models  # noqa: F401
    from .routes import api, auth, clienti, lavori, main, preventivi, tasks

    register_auth_endpoint_aliases(app)
    register_legacy_endpoint_aliases(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(clienti.bp)
    app.register_blueprint(lavori.bp)
    app.register_blueprint(preventivi.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(api.bp)
    register_auth_guards(app)

    # Compatibilita temporanea con il comportamento storico del monolite.
    # Da rimuovere quando il progetto usera esclusivamente Flask-Migrate.
    if "db" not in sys.argv:
        with app.app_context():
            db.create_all()

    return app


def register_template_filters(app):
    @app.template_filter()
    def euroFormat(value):
        value = float(value)
        return "{:.2f}".format(value).replace(".", ",")

    @app.template_filter("nl2br")
    def nl2br_filter(text):
        if text:
            return text.replace("\n", "<br>\n")
        return ""


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
