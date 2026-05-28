import click
from flask.cli import with_appcontext

from .extensions import db
from .models import Fattura, FinancialMovement, User


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

    @app.cli.command("migrate-finance-gross")
    @with_appcontext
    def migrate_finance_gross():
        """Aggiorna i movimenti finance auto-generati da fatture all'importo
        lordo IVA inclusa. Non modifica movimenti manuali."""
        from .finance_service import invoice_effective_amount

        source_types = ("sent_invoice", "received_invoice")
        movements = FinancialMovement.query.filter(
            FinancialMovement.source_type.in_(source_types)
        ).all()

        updated = 0
        skipped = 0
        errors = 0

        for mov in movements:
            fattura = Fattura.query.get(mov.source_id)
            if not fattura:
                click.echo(
                    f"  SKIP movimento {mov.id}: fattura {mov.source_id} non trovata"
                )
                skipped += 1
                continue
            try:
                effective = invoice_effective_amount(fattura)
                if mov.amount != effective:
                    old = mov.amount
                    mov.amount = effective
                    click.echo(
                        f"  AGGIORNATO movimento {mov.id} "
                        f"({mov.source_type} fattura {fattura.id}): "
                        f"{old} -> {gross}"
                    )
                    updated += 1
                else:
                    skipped += 1
            except Exception as e:
                click.echo(f"  ERRORE movimento {mov.id}: {e}")
                errors += 1

        db.session.commit()
        click.echo(
            f"\nFatto: {updated} aggiornati, "
            f"{skipped} invariati, {errors} errori"
        )
