from math import ceil

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..auth import login_required, role_required
from ..extensions import db
from ..mail_service import (
    MailConfigurationError,
    MailSyncError,
    credentials_key_configured,
    encrypt_password,
    send_email,
    sync_inbox,
)
from ..models import Cliente, EmailAccount, EmailMessage, Lavoro
from ..utils.parsing import parse_optional_id


bp = Blueprint("mail", __name__)


def bool_from_form(name, default=False):
    if name not in request.form:
        return default
    return request.form.get(name) == "on"


def mail_choices():
    return {
        "accounts": EmailAccount.query.filter_by(is_active=True)
        .order_by(EmailAccount.label.asc())
        .all(),
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "lavori": Lavoro.query.order_by(Lavoro.descrizione.asc()).all(),
    }


def normalize_page_number(value, default=1):
    try:
        page = int(value)
    except (TypeError, ValueError):
        return default
    return max(page, 1)


def normalize_per_page(value, default=25, maximum=25):
    try:
        per_page = int(value)
    except (TypeError, ValueError):
        return default
    if per_page < 1:
        return default
    return min(per_page, maximum)


def build_mail_query_args(**kwargs):
    args = {}
    for key, value in kwargs.items():
        if value in (None, "", 0):
            continue
        args[key] = value
    return args


def apply_account_form(account):
    account.label = (request.form.get("label") or "").strip()
    account.email_address = (request.form.get("email_address") or "").strip().lower()
    account.imap_host = (request.form.get("imap_host") or "").strip()
    account.imap_port = int(request.form.get("imap_port") or 993)
    account.imap_use_ssl = bool_from_form("imap_use_ssl", default=False)
    account.smtp_host = (request.form.get("smtp_host") or "").strip()
    account.smtp_port = int(request.form.get("smtp_port") or 587)
    account.smtp_use_tls = bool_from_form("smtp_use_tls", default=False)
    account.username = (request.form.get("username") or "").strip()
    account.is_active = bool_from_form("is_active", default=False)

    password = request.form.get("password") or ""
    if password:
        account.password_encrypted = encrypt_password(password)
    elif account.id is None:
        raise MailConfigurationError("La password/app password e obbligatoria per un nuovo account.")

    if not account.label:
        raise ValueError("Il nome account e obbligatorio.")
    if not account.email_address:
        raise ValueError("L'indirizzo email account e obbligatorio.")
    if not account.imap_host or not account.smtp_host:
        raise ValueError("Host IMAP e SMTP sono obbligatori.")
    if not account.username:
        raise ValueError("Username email obbligatorio.")


def apply_message_links(message):
    cliente_id = parse_optional_id(request.form.get("cliente_id"))
    lavoro_id = parse_optional_id(request.form.get("lavoro_id"))

    if lavoro_id and cliente_id is None:
        lavoro = db.session.get(Lavoro, lavoro_id)
        cliente_id = lavoro.cliente_id if lavoro else None

    message.cliente_id = cliente_id
    message.lavoro_id = lavoro_id


@bp.get("/mail")
@login_required
def mail_index():
    query = EmailMessage.query
    account_id = request.args.get("account_id", type=int)
    cliente_id = request.args.get("cliente_id", type=int)
    lavoro_id = request.args.get("lavoro_id", type=int)
    q = (request.args.get("q") or "").strip()
    page = normalize_page_number(request.args.get("page"), default=1)
    per_page = normalize_per_page(request.args.get("per_page"), default=25, maximum=25)

    if account_id:
        query = query.filter_by(account_id=account_id)
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    if lavoro_id:
        query = query.filter_by(lavoro_id=lavoro_id)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            db.or_(
                EmailMessage.subject.ilike(pattern),
                EmailMessage.from_address.ilike(pattern),
                EmailMessage.to_addresses.ilike(pattern),
            )
        )

    total_messages = query.order_by(None).count()
    total_pages = ceil(total_messages / per_page) if total_messages else 0
    if total_pages:
        page = min(page, total_pages)
    else:
        page = 1

    messages = query.order_by(
        EmailMessage.received_at.desc().nullslast(),
        EmailMessage.sent_at.desc().nullslast(),
        EmailMessage.id.desc(),
    ).offset((page - 1) * per_page).limit(per_page).all()

    query_args = build_mail_query_args(
        account_id=account_id,
        cliente_id=cliente_id,
        lavoro_id=lavoro_id,
        q=q,
        per_page=per_page,
    )

    prev_url = (
        url_for("mail.mail_index", page=page - 1, **query_args)
        if total_messages and page > 1
        else None
    )
    next_url = (
        url_for("mail.mail_index", page=page + 1, **query_args)
        if total_pages and page < total_pages
        else None
    )
    return render_template(
        "mail.html",
        messages=messages,
        total_messages=total_messages,
        current_page=page,
        total_pages=total_pages,
        per_page=per_page,
        prev_url=prev_url,
        next_url=next_url,
        selected_account_id=account_id,
        selected_cliente_id=cliente_id,
        selected_lavoro_id=lavoro_id,
        q=q,
        **mail_choices(),
    )


@bp.get("/mail/<int:message_id>")
@login_required
def mail_detail(message_id):
    message = EmailMessage.query.get_or_404(message_id)
    if message.direction == "inbound" and not message.is_read and g.current_user.role != "readonly":
        message.is_read = True
        db.session.commit()
    return render_template("mail_detail.html", message=message, **mail_choices())


@bp.route("/mail/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def mail_new():
    error = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        account = EmailAccount.query.get_or_404(request.form.get("account_id", type=int))
        try:
            sent_message = send_email(
                account=account,
                to_addresses=(request.form.get("to_addresses") or "").strip(),
                cc_addresses=(request.form.get("cc_addresses") or "").strip() or None,
                subject=(request.form.get("subject") or "").strip(),
                body=(request.form.get("body") or "").strip(),
            )
            apply_message_links(sent_message)
            db.session.add(sent_message)
            db.session.commit()
            return redirect(url_for("mail.mail_detail", message_id=sent_message.id))
        except (MailConfigurationError, MailSyncError, ValueError) as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "mail_compose.html",
        page_title="Nuova email",
        form_action=url_for("mail.mail_new"),
        error=error,
        form_data=form_data,
        reply_to_message=None,
        **mail_choices(),
    )


@bp.route("/mail/<int:message_id>/reply", methods=["GET", "POST"])
@role_required("admin", "operatore")
def mail_reply(message_id):
    original = EmailMessage.query.get_or_404(message_id)
    error = None
    form_data = {
        "account_id": original.account_id,
        "to_addresses": original.reply_to or original.from_address,
        "subject": original.subject if (original.subject or "").lower().startswith("re:") else f"Re: {original.subject or ''}",
        "body": f"\n\n--- Messaggio originale ---\n{original.body_text or ''}",
        "cliente_id": original.cliente_id,
        "lavoro_id": original.lavoro_id,
    }

    if request.method == "POST":
        form_data.update(request.form.to_dict())
        account = EmailAccount.query.get_or_404(request.form.get("account_id", type=int))
        try:
            sent_message = send_email(
                account=account,
                to_addresses=(request.form.get("to_addresses") or "").strip(),
                cc_addresses=(request.form.get("cc_addresses") or "").strip() or None,
                subject=(request.form.get("subject") or "").strip(),
                body=(request.form.get("body") or "").strip(),
                reply_to_message=original,
            )
            apply_message_links(sent_message)
            db.session.add(sent_message)
            db.session.commit()
            return redirect(url_for("mail.mail_detail", message_id=sent_message.id))
        except (MailConfigurationError, MailSyncError, ValueError) as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "mail_compose.html",
        page_title="Rispondi email",
        form_action=url_for("mail.mail_reply", message_id=original.id),
        error=error,
        form_data=form_data,
        reply_to_message=original,
        **mail_choices(),
    )


@bp.post("/mail/<int:message_id>/link")
@role_required("admin", "operatore")
def mail_link(message_id):
    message = EmailMessage.query.get_or_404(message_id)
    apply_message_links(message)
    db.session.commit()
    return redirect(url_for("mail.mail_detail", message_id=message.id))


@bp.get("/mail/accounts")
@role_required("admin")
def mail_accounts():
    accounts = EmailAccount.query.order_by(EmailAccount.label.asc()).all()
    return render_template("mail_accounts.html", accounts=accounts)


@bp.route("/mail/accounts/new", methods=["GET", "POST"])
@role_required("admin")
def mail_account_new():
    account = EmailAccount(imap_port=993, imap_use_ssl=True, smtp_port=587, smtp_use_tls=True, is_active=True)
    error = None
    if request.method == "GET" and not credentials_key_configured():
        error = (
            "EMAIL_CREDENTIALS_KEY non configurata. Imposta una chiave Fernet valida "
            "prima di salvare la password dell'account."
        )

    if request.method == "POST":
        try:
            account.created_by = g.current_user.id if g.get("current_user") else None
            apply_account_form(account)
            db.session.add(account)
            db.session.commit()
            return redirect(url_for("mail.mail_accounts"))
        except (ValueError, MailConfigurationError) as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "mail_account_form.html",
        account=account,
        error=error,
        form_action=url_for("mail.mail_account_new"),
        page_title="Nuovo account email",
        submit_label="Salva account",
    )


@bp.route("/mail/accounts/<int:account_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def mail_account_edit(account_id):
    account = EmailAccount.query.get_or_404(account_id)
    error = None

    if request.method == "POST":
        try:
            apply_account_form(account)
            db.session.commit()
            return redirect(url_for("mail.mail_accounts"))
        except (ValueError, MailConfigurationError) as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "mail_account_form.html",
        account=account,
        error=error,
        form_action=url_for("mail.mail_account_edit", account_id=account.id),
        page_title="Modifica account email",
        submit_label="Salva modifiche",
    )


@bp.post("/mail/accounts/<int:account_id>/delete")
@role_required("admin")
def mail_account_delete(account_id):
    account = EmailAccount.query.get_or_404(account_id)
    try:
        messages = EmailMessage.query.filter_by(account_id=account.id).all()
        for msg in messages:
            db.session.delete(msg)
        db.session.delete(account)
        db.session.commit()
        flash("Account email eliminato con successo.", "success")
    except Exception:
        db.session.rollback()
        flash("Impossibile eliminare l'account. Operazione annullata.", "danger")
    return redirect(url_for("mail.mail_accounts"))


@bp.post("/mail/accounts/<int:account_id>/sync")
@role_required("admin")
def mail_account_sync(account_id):
    account = EmailAccount.query.get_or_404(account_id)
    try:
        result = sync_inbox(account)
        flash(
            f"Sync completata: {result['imported']} nuove email, {result['skipped']} gia presenti o ignorate.",
            "success",
        )
    except (MailConfigurationError, MailSyncError) as exc:
        flash(str(exc), "danger")
    return redirect(url_for("mail.mail_accounts"))
