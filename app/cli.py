import click
from flask.cli import with_appcontext

from .extensions import db
from .models import User


def register_cli(app):
    @app.cli.command("create-admin")
    @click.option("--email", required=True, help="Email del primo admin.")
    @click.option("--password", required=True, help="Password del primo admin.")
    @click.option("--name", default="Admin", show_default=True, help="Nome utente.")
    @with_appcontext
    def create_admin(email, password, name):
        email = (email or "").strip().lower()
        password = password or ""

        if not email:
            raise click.ClickException("Email obbligatoria.")
        if not password:
            raise click.ClickException("Password obbligatoria.")
        if User.query.filter_by(email=email).first() is not None:
            raise click.ClickException(f"Esiste gia un utente con email {email}.")

        user = User(name=name, email=email, role="admin")
        if user.role != "admin":
            raise click.ClickException("Il primo utente deve avere ruolo admin.")

        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin creato: {email}")
