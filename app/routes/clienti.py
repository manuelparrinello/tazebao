import os
from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_file, url_for

from ..auth import login_required, role_required
from ..extensions import db
from ..models import CalendarEvent, Cliente, EditorialPublication, EmailLog, EmailMessage, FinancialMovement, Lavoro, Moodboard, Preventivo, Task
from ..storage_utils import build_breadcrumb, get_cliente_relative_path, list_entries, normalize_subdir, resolve_collision, safe_path, slugify, ensure_storage_dir


bp = Blueprint("clienti", __name__)


@bp.route("/clienti/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def nuovo_cliente():
    if request.method == "POST":
        nome = request.form.get("nome").title()
        ragsoc = request.form.get("ragsoc").title()
        indirizzo = request.form.get("indirizzo").title()
        cap = request.form.get("cap")
        citta = request.form.get("citta").title()
        provincia = request.form.get("provincia").upper()
        email = request.form.get("email").lower()
        telefono = request.form.get("telefono")
        p_iva = request.form.get("p_iva")
        sdi = request.form.get("sdi")
        pec = request.form.get("pec")
        colore = request.form.get("colore")
        note = request.form.get("note")

        nuovo_cliente = Cliente(
            name=nome,
            ragsoc=ragsoc,
            indirizzo=indirizzo,
            cap=cap,
            citta=citta,
            provincia=provincia,
            p_iva=p_iva,
            sdi=sdi,
            pec=pec,
            telefono=telefono,
            email=email,
            note=note,
            colore=colore,
        )
        db.session.add(nuovo_cliente)
        db.session.commit()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
            return (
                jsonify(
                    {
                        "message": "Cliente aggiunto con successo!",
                        "data": {
                            "nome": nome,
                            "ragsoc": ragsoc,
                            "telefono": telefono,
                            "email": email,
                            "note": note,
                            "colore": colore,
                        },
                    }
                ),
                201,
            )

        return redirect(url_for("clienti.cliente_page", cliente_id=nuovo_cliente.id))

    if request.method == "GET":
        return render_template("cliente_new.html")


@bp.route("/clienti")
@login_required
def clienti():
    clienti_list = Cliente.query.all()
    return render_template("clienti.html", clienti=clienti_list)


@bp.route("/clienti/<int:cliente_id>")
@login_required
def cliente_page(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    lavori = (
        Lavoro.query.filter_by(cliente_id=cliente_id)
        .order_by(Lavoro.id.desc())
        .limit(10)
        .all()
    )
    tasks = (
        Task.query.filter_by(cliente_id=cliente_id)
        .order_by(Task.updated_at.desc(), Task.created_at.desc())
        .limit(10)
        .all()
    )
    eventi = (
        CalendarEvent.query.filter_by(cliente_id=cliente_id)
        .order_by(CalendarEvent.start_datetime.desc())
        .limit(10)
        .all()
    )
    editorial_publications = (
        EditorialPublication.query.filter_by(cliente_id=cliente_id)
        .filter(EditorialPublication.publication_date >= date.today())
        .order_by(EditorialPublication.publication_date.asc(), EditorialPublication.id.asc())
        .limit(10)
        .all()
    )
    preventivi = (
        Preventivo.query.filter_by(cliente_id=cliente_id)
        .order_by(Preventivo.data_creazione.desc())
        .limit(10)
        .all()
    )
    preventivi_esterni = (
        Lavoro.query.filter(
            Lavoro.cliente_id == cliente_id,
            Lavoro.preventivo_pdf_path.isnot(None),
            Lavoro.preventivo_pdf_path != "",
        )
        .order_by(Lavoro.data_inizio.desc().nullslast(), Lavoro.id.desc())
        .limit(10)
        .all()
    )
    movimenti = (
        FinancialMovement.query.filter_by(cliente_id=cliente_id)
        .order_by(FinancialMovement.movement_date.desc(), FinancialMovement.id.desc())
        .limit(10)
        .all()
    )
    email_logs = (
        EmailLog.query.filter_by(cliente_id=cliente_id)
        .order_by(EmailLog.sent_at.desc(), EmailLog.id.desc())
        .limit(5)
        .all()
    )
    mail_messages = (
        EmailMessage.query.filter_by(cliente_id=cliente_id)
        .order_by(
            EmailMessage.received_at.desc().nullslast(),
            EmailMessage.sent_at.desc().nullslast(),
            EmailMessage.id.desc(),
        )
        .limit(10)
        .all()
    )

    quick_actions = {
        "nuovo_lavoro": url_for("nuovo_lavoro", cliente_id=cliente.id),
        "nuovo_task": url_for("tasks.task_new", cliente_id=cliente.id),
        "nuovo_evento": url_for("calendar.calendar_new", cliente_id=cliente.id),
        "nuovo_preventivo": url_for("nuovo_preventivo", cliente_id=cliente.id),
        "nuovo_movimento": url_for("finance.finance_new", cliente_id=cliente.id),
        "nuova_comunicazione": url_for("emails.emails_new", cliente_id=cliente.id),
            "nuova_pubblicazione": url_for(
                "editorial_calendar.editorial_new",
                cliente_id=cliente.id,
            ),
            "nuova_email": url_for("mail.mail_new", cliente_id=cliente.id),
        }

    return render_template(
        "cliente.html",
        cliente=cliente,
        lavori=lavori,
        tasks=tasks,
        eventi=eventi,
        editorial_publications=editorial_publications,
        preventivi=preventivi,
        preventivi_esterni=preventivi_esterni,
        movimenti=movimenti,
        email_logs=email_logs,
        mail_messages=mail_messages,
        quick_actions=quick_actions,
    )


@bp.delete("/clienti/<int:cliente_id>")
@role_required("admin", "operatore")
def cliente_delete(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    editorial_count = EditorialPublication.query.filter_by(cliente_id=cliente_id).count()
    if editorial_count > 0:
        return jsonify({
            "message": f"Impossibile eliminare il cliente: ci sono {editorial_count} pubblicazioni editoriali collegate. Rimuovi prima i collegamenti.",
            "error": "cliente_has_editorial_publications",
        }), 400

    CalendarEvent.query.filter_by(cliente_id=cliente_id).update(
        {CalendarEvent.cliente_id: None}
    )
    FinancialMovement.query.filter_by(cliente_id=cliente_id).update(
        {FinancialMovement.cliente_id: None}
    )
    EmailLog.query.filter_by(cliente_id=cliente_id).update(
        {EmailLog.cliente_id: None}
    )
    EmailMessage.query.filter_by(cliente_id=cliente_id).update(
        {EmailMessage.cliente_id: None}
    )
    Moodboard.query.filter_by(cliente_id=cliente_id).update(
        {Moodboard.cliente_id: None}
    )
    Task.query.filter_by(cliente_id=cliente_id).update(
        {Task.cliente_id: None}
    )

    db.session.delete(cliente)
    db.session.commit()
    return jsonify({"message": "Cliente eliminato con successo"})


@bp.route("/clienti/edit/<int:cliente_id>", methods=["GET", "PUT"])
@role_required("admin", "operatore")
def cliente_edit(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == "GET":
        return render_template("cliente_edit.html", cliente=cliente)
    if request.method == "PUT":
        dataFromJS = request.get_json()
        if not dataFromJS:
            return jsonify({"messaggio": "Nessun dato ricevuto"}), 400
        cliente.name = dataFromJS.get("nomeCliente", cliente.name)
        cliente.email = dataFromJS.get("email", cliente.email)
        cliente.telefono = dataFromJS.get("telefono", cliente.telefono)
        cliente.note = dataFromJS.get("note", cliente.note)
        cliente.colore = dataFromJS.get("colore", cliente.colore)
        try:
            db.session.commit()
            return (
                jsonify(
                    {"messaggio": f"Cliente {cliente.name} aggiornato con successo"}
                ),
                200,
            )
        except Exception as e:
            db.session.rollback()
            return jsonify({"messaggio": f"Errore: {str(e)}"}), 500


@bp.route("/clienti/<int:cliente_id>/cartella/crea", methods=["POST"])
@role_required("admin", "operatore")
def cliente_cartella_crea(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    wants_json = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
    )

    if cliente.folder_path:
        if wants_json:
            return jsonify({"messaggio": "Cartella gia esistente.", "folder_path": cliente.folder_path}), 200
        flash("Cartella gia esistente.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    try:
        slug = slugify(cliente.name) or f"cliente-{cliente.id}"
        rel_path = get_cliente_relative_path(cliente.id, slug)
        rel_path = resolve_collision(rel_path)
        ensure_storage_dir(rel_path)
    except (OSError, IOError) as e:
        if wants_json:
            return jsonify({"error": f"Errore filesystem: {str(e)}"}), 500
        flash(f"Errore nella creazione della cartella: {str(e)}", "danger")
        return redirect(url_for("cliente_page", cliente_id=cliente.id))

    cliente.folder_path = rel_path
    db.session.commit()

    if wants_json:
        return jsonify({"messaggio": "Cartella cliente creata correttamente.", "folder_path": rel_path}), 201

    flash("Cartella cliente creata correttamente.", "success")
    return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))


@bp.route("/clienti/<int:cliente_id>/cartella")
@login_required
def cliente_cartella(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    folder_active = bool(cliente.folder_path)
    subdir = normalize_subdir(request.args.get("subdir", ""))

    if subdir is None:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    if folder_active and subdir:
        rel_path = os.path.join(cliente.folder_path, subdir).replace("\\", "/")
        abs_path = safe_path(rel_path)
        if not abs_path or not os.path.isdir(abs_path):
            flash("Cartella non trovata.", "warning")
            return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))
    elif folder_active:
        abs_path = safe_path(cliente.folder_path)
    else:
        abs_path = None

    entries = list_entries(abs_path) if abs_path else []
    breadcrumb = build_breadcrumb(
        subdir,
        lambda **kw: url_for("clienti.cliente_cartella", cliente_id=cliente.id, **kw),
        "Cartella cliente",
    )

    return render_template(
        "cliente_cartella.html",
        cliente=cliente,
        entries=entries,
        folder_active=folder_active,
        subdir=subdir,
        breadcrumb=breadcrumb,
    )


@bp.route("/clienti/<int:cliente_id>/cartella/download/<path:filename>")
@login_required
def cliente_cartella_download(cliente_id, filename):
    cliente = Cliente.query.get_or_404(cliente_id)
    if not cliente.folder_path:
        return jsonify({"error": "Cartella non esistente."}), 404

    rel_path = os.path.join(cliente.folder_path, filename).replace("\\", "/")
    abs_path = safe_path(rel_path)
    if not abs_path or not os.path.isfile(abs_path):
        return jsonify({"error": "File non trovato."}), 404

    download_name = os.path.basename(filename)
    return send_file(abs_path, as_attachment=True, download_name=download_name)
