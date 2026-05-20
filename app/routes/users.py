from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for

from ..auth import role_required
from ..extensions import db
from ..models import (
    EmailAccount,
    EmailLog,
    FinancialMovement,
    User,
    VALID_USER_ROLES,
)


bp = Blueprint("users", __name__)

ADMIN_ROLE = "admin"


def normalize_email(value):
    return (value or "").strip().lower()


def normalize_name(value):
    return (value or "").strip() or None


def parse_bool(value):
    return str(value).lower() in {"1", "true", "on", "yes"}


def render_user_form(template_name, **context):
    return render_template(template_name, roles=VALID_USER_ROLES, **context)


def validate_role(role):
    return role in VALID_USER_ROLES


def active_admin_count():
    return User.query.filter_by(role=ADMIN_ROLE, is_active=True).count()


def would_remove_last_admin(user, new_role, new_is_active):
    if user.role != ADMIN_ROLE or not user.is_active:
        return False
    if new_role == ADMIN_ROLE and new_is_active:
        return False
    return active_admin_count() <= 1


def can_soft_delete_user(user):
    if user.id == g.current_user.id:
        flash("Non puoi eliminare il tuo account.", "danger")
        return False
    if would_remove_last_admin(user, user.role, False):
        flash("Non puoi eliminare l'ultimo admin attivo.", "danger")
        return False
    return True


def user_has_erp_links(user):
    checks = (
        FinancialMovement.query.filter_by(created_by=user.id).first(),
        EmailAccount.query.filter_by(created_by=user.id).first(),
        EmailLog.query.filter_by(created_by=user.id).first(),
    )
    return any(checks)


def can_destroy_user(user):
    if user.id == g.current_user.id:
        flash("Non puoi eliminare definitivamente il tuo account.", "danger")
        return False
    if would_remove_last_admin(user, user.role, False):
        flash("Non puoi eliminare definitivamente l'ultimo admin attivo.", "danger")
        return False
    if user_has_erp_links(user):
        flash("Utente collegato a dati ERP, disattivalo invece.", "warning")
        return False
    return True


def user_form_values(user=None, source=None):
    source = source or {}
    return {
        "name": (source.get("name") if source else (user.name if user else "")) or "",
        "email": (source.get("email") if source else (user.email if user else "")) or "",
        "role": (source.get("role") if source else (user.role if user else "readonly")) or "readonly",
        "is_active": source.get("is_active")
        if source
        else ("on" if (user.is_active if user else True) else ""),
    }


@bp.get("/users")
@role_required("admin")
def users_index():
    users = User.query.order_by(
        User.is_active.desc(),
        User.role.asc(),
        User.id.asc(),
    ).all()
    return render_template("users.html", users=users)


@bp.route("/users/new", methods=["GET", "POST"])
@role_required("admin")
def users_new():
    if request.method == "POST":
        name = normalize_name(request.form.get("name"))
        email = normalize_email(request.form.get("email"))
        role = request.form.get("role") or "readonly"
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm") or ""
        is_active = parse_bool(request.form.get("is_active"))
        form_data = user_form_values(source=request.form)

        if not email:
            flash("Email obbligatoria.", "danger")
            return render_user_form("user_form.html", user=None, form_data=form_data), 400
        if not password:
            flash("Password obbligatoria.", "danger")
            return render_user_form("user_form.html", user=None, form_data=form_data), 400
        if password != password_confirm:
            flash("Le password non coincidono.", "danger")
            return render_user_form("user_form.html", user=None, form_data=form_data), 400
        if not validate_role(role):
            flash("Ruolo non valido.", "danger")
            return render_user_form("user_form.html", user=None, form_data=form_data), 400
        if User.query.filter(db.func.lower(User.email) == email.lower()).first():
            flash("Esiste gia un utente con questa email.", "danger")
            return render_user_form("user_form.html", user=None, form_data=form_data), 400

        user = User(name=name, email=email, role=role, is_active=is_active)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Utente creato con successo.", "success")
        return redirect(url_for("users.users_index"))

    return render_user_form("user_form.html", user=None, form_data=user_form_values())


@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def users_edit(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash("Utente non trovato.", "danger")
        return redirect(url_for("users.users_index"))

    if request.method == "POST":
        name = normalize_name(request.form.get("name"))
        email = normalize_email(request.form.get("email"))
        role = request.form.get("role") or "readonly"
        is_active = parse_bool(request.form.get("is_active"))
        form_data = user_form_values(user=user, source=request.form)

        if not email:
            flash("Email obbligatoria.", "danger")
            return render_user_form("user_form.html", user=user, form_data=form_data), 400
        if not validate_role(role):
            flash("Ruolo non valido.", "danger")
            return render_user_form("user_form.html", user=user, form_data=form_data), 400

        duplicate = User.query.filter(
            db.func.lower(User.email) == email.lower(),
            User.id != user.id,
        ).first()
        if duplicate:
            flash("Esiste gia un utente con questa email.", "danger")
            return render_user_form("user_form.html", user=user, form_data=form_data), 400

        if user.id == g.current_user.id and not is_active:
            flash("Non puoi disattivare il tuo account.", "danger")
            return render_user_form("user_form.html", user=user, form_data=form_data), 400

        if would_remove_last_admin(user, role, is_active):
            flash("Non puoi rimuovere l'ultimo admin attivo.", "danger")
            return render_user_form("user_form.html", user=user, form_data=form_data), 400

        user.name = name
        user.email = email
        user.role = role
        user.is_active = is_active
        db.session.commit()
        flash("Utente aggiornato.", "success")
        return redirect(url_for("users.users_index"))

    return render_user_form("user_form.html", user=user, form_data=user_form_values(user=user))


@bp.post("/users/<int:user_id>/deactivate")
@role_required("admin")
def users_deactivate(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash("Utente non trovato.", "danger")
        return redirect(url_for("users.users_index"))

    if user.id == g.current_user.id:
        flash("Non puoi disattivare il tuo account.", "danger")
        return redirect(url_for("users.users_index"))

    if would_remove_last_admin(user, user.role, False):
        flash("Non puoi disattivare l'ultimo admin attivo.", "danger")
        return redirect(url_for("users.users_index"))

    try:
        user.is_active = False
        db.session.commit()
        flash("Utente disattivato.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore disattivazione utente %d", user_id)
        flash("Impossibile disattivare l'utente. Operazione annullata.", "danger")
    return redirect(url_for("users.users_index"))


@bp.post("/users/<int:user_id>/delete")
@role_required("admin")
def users_delete(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash("Utente non trovato.", "danger")
        return redirect(url_for("users.users_index"))

    if not can_soft_delete_user(user):
        return redirect(url_for("users.users_index"))

    try:
        user.is_active = False
        db.session.commit()
        flash("Utente eliminato dalla lista attiva. L'account è stato disattivato.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore soft-delete utente %d", user_id)
        flash("Impossibile eliminare l'utente. Operazione annullata.", "danger")
    return redirect(url_for("users.users_index"))


@bp.post("/users/<int:user_id>/destroy")
@role_required("admin")
def users_destroy(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash("Utente non trovato.", "danger")
        return redirect(url_for("users.users_index"))

    if not can_destroy_user(user):
        return redirect(url_for("users.users_index"))

    try:
        db.session.delete(user)
        db.session.commit()
        flash("Utente eliminato definitivamente.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore eliminazione definitiva utente %d", user_id)
        flash("Impossibile eliminare definitivamente l'utente. Operazione annullata.", "danger")
    return redirect(url_for("users.users_index"))


@bp.post("/users/<int:user_id>/activate")
@role_required("admin")
def users_activate(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash("Utente non trovato.", "danger")
        return redirect(url_for("users.users_index"))

    user.is_active = True
    db.session.commit()
    flash("Utente attivato.", "success")
    return redirect(url_for("users.users_index"))


@bp.route("/users/<int:user_id>/password", methods=["GET", "POST"])
@role_required("admin")
def users_password(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash("Utente non trovato.", "danger")
        return redirect(url_for("users.users_index"))

    if request.method == "POST":
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm") or ""

        if not password:
            flash("Password obbligatoria.", "danger")
            return render_user_form("user_password.html", user=user), 400
        if password != password_confirm:
            flash("Le password non coincidono.", "danger")
            return render_user_form("user_password.html", user=user), 400

        user.set_password(password)
        db.session.commit()
        flash("Password aggiornata.", "success")
        return redirect(url_for("users.users_index"))

    return render_user_form("user_password.html", user=user)
