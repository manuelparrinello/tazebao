import os
import shutil
from datetime import date

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for

from ..auth import login_required, role_required
from ..extensions import db
from ..finance_service import cliente_marginality
from ..models import CalendarEvent, Cliente, EditorialPublication, EmailLog, EmailMessage, Fattura, FinancialMovement, Lavoro, Moodboard, Preventivo, Task
from ..storage_utils import build_breadcrumb, create_subfolder, delete_empty_storage_folder, delete_storage_file, get_cliente_relative_path, list_entries, normalize_subdir, rename_storage_entry, resolve_collision, safe_path, save_uploaded_storage_file, save_uploaded_storage_files, slugify, ensure_storage_dir


bp = Blueprint("clienti", __name__)


@bp.route("/clienti/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def nuovo_cliente():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        if not nome:
            flash("Il nome del cliente è obbligatorio.", "danger")
            return render_template("cliente_new.html")
        nome = nome.title()
        ragsoc = (request.form.get("ragsoc") or "").strip().title()
        indirizzo = (request.form.get("indirizzo") or "").strip().title()
        cap = (request.form.get("cap") or "").strip()
        citta = (request.form.get("citta") or "").strip().title()
        provincia = (request.form.get("provincia") or "").strip().upper()
        email = (request.form.get("email") or "").strip().lower()
        telefono = (request.form.get("telefono") or "").strip()
        p_iva = (request.form.get("p_iva") or "").strip()
        sdi = (request.form.get("sdi") or "").strip()
        pec = (request.form.get("pec") or "").strip()
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
    fatture = (
        Fattura.query.filter_by(cliente_id=cliente_id)
        .order_by(Fattura.data_emissione.desc(), Fattura.id.desc())
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

    today = date.today()
    situazione = {
        "task_aperte": Task.query.filter(
            Task.cliente_id == cliente_id,
            Task.status.in_(["da_fare", "in_corso", "in_revisione"]),
        ).count(),
        "task_scadute": Task.query.filter(
            Task.cliente_id == cliente_id,
            Task.due_date.isnot(None),
            Task.due_date < today,
            ~Task.status.in_(["completata", "annullata"]),
        ).count(),
        "preventivi_aperti": Preventivo.query.filter(
            Preventivo.cliente_id == cliente_id,
            Preventivo.stato.in_(["bozza", "inviato", "in_attesa"]),
        ).count(),
        "lavori_attivi": Lavoro.query.filter(
            Lavoro.cliente_id == cliente_id,
            Lavoro.stato != "Completato",
        ).count(),
        "prossime_pubblicazioni": EditorialPublication.query.filter(
            EditorialPublication.cliente_id == cliente_id,
            EditorialPublication.publication_date >= today,
            ~EditorialPublication.status.in_(["pubblicato", "annullato"]),
        ).count(),
    }

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
        fatture=fatture,
        email_logs=email_logs,
        mail_messages=mail_messages,
        quick_actions=quick_actions,
        marg=cliente_marginality(cliente_id),
        situazione=situazione,
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

    if cliente.folder_path:
        abs_path = safe_path(cliente.folder_path)
        if abs_path and os.path.exists(abs_path):
            try:
                shutil.rmtree(abs_path)
            except OSError as e:
                return jsonify({"error": f"Impossibile eliminare la cartella: {str(e)}"}), 500

    try:
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente eliminato con successo"})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore eliminazione cliente %d", cliente_id)
        return jsonify({"error": "Impossibile completare l'eliminazione del cliente."}), 500


@bp.route("/clienti/edit/<int:cliente_id>", methods=["GET", "PUT"])
@role_required("admin", "operatore")
def cliente_edit(cliente_id):
    # NOTA: folder_path NON viene aggiornato al rename del cliente.
    # Il path su disco resta stabile per evitare rottura percorsi esterni/sync.
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


@bp.route("/clienti/<int:cliente_id>/cartella/upload", methods=["POST"])
@role_required("admin", "operatore")
def cliente_cartella_upload(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if not cliente.folder_path:
        flash("Nessuna cartella creata per questo cliente.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    subdir = normalize_subdir(request.args.get("subdir", ""))
    if subdir is None:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    rel_path = os.path.join(cliente.folder_path, subdir).replace("\\", "/") if subdir else cliente.folder_path
    abs_path = safe_path(rel_path)
    if not abs_path or not os.path.isdir(abs_path):
        flash("Cartella non trovata.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    files = request.files.getlist("file")
    if not files or all(not f or not f.filename for f in files):
        flash("Nessun file selezionato.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id, subdir=subdir or None))

    results = save_uploaded_storage_files(files, abs_path)

    n_ok = len(results["ok"])
    n_renamed = results["renamed"]
    if n_ok > 0:
        msg = f"{n_ok} file caricati correttamente."
        if n_renamed > 0:
            msg += f" {n_renamed} rinominato{'i' if n_renamed > 1 else ''} per evitare sovrascrittura."
        flash(msg, "success")

    for err in results["errors"]:
        flash(err, "danger")

    return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id, subdir=subdir or None))


@bp.route("/clienti/<int:cliente_id>/cartella/sottocartella/crea", methods=["POST"])
@role_required("admin", "operatore")
def cliente_cartella_sottocartella_crea(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if not cliente.folder_path:
        flash("Nessuna cartella creata per questo cliente.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    subdir = normalize_subdir(request.args.get("subdir", ""))
    if subdir is None:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    rel_path = os.path.join(cliente.folder_path, subdir).replace("\\", "/") if subdir else cliente.folder_path
    abs_path = safe_path(rel_path)
    if not abs_path or not os.path.isdir(abs_path):
        flash("Cartella non trovata.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    folder_name = request.form.get("nome_cartella", "")
    try:
        create_subfolder(abs_path, folder_name)
        flash("Cartella creata correttamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id, subdir=subdir or None))


@bp.route("/clienti/<int:cliente_id>/cartella/rinomina", methods=["POST"])
@role_required("admin", "operatore")
def cliente_cartella_rename(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if not cliente.folder_path:
        flash("Nessuna cartella creata per questo cliente.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    subdir = normalize_subdir(request.args.get("subdir", ""))
    if subdir is None:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    rel_path = os.path.join(cliente.folder_path, subdir).replace("\\", "/") if subdir else cliente.folder_path
    abs_path = safe_path(rel_path)
    if not abs_path or not os.path.isdir(abs_path):
        flash("Cartella non trovata.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    old_name = request.form.get("old_name", "").strip()
    new_name = request.form.get("new_name", "").strip()

    is_file = os.path.isfile(os.path.join(abs_path, old_name)) if old_name else False
    try:
        rename_storage_entry(abs_path, old_name, new_name)
        flash("File rinominato correttamente." if is_file else "Cartella rinominata correttamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id, subdir=subdir or None))


@bp.route("/clienti/<int:cliente_id>/cartella/elimina/<path:filename>", methods=["POST"])
@role_required("admin", "operatore")
def cliente_cartella_delete_file(cliente_id, filename):
    cliente = Cliente.query.get_or_404(cliente_id)
    if not cliente.folder_path:
        flash("Nessuna cartella creata per questo cliente.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    rel_path = os.path.join(cliente.folder_path, filename).replace("\\", "/")
    abs_path = safe_path(rel_path)
    if not abs_path:
        flash("File non trovato.", "danger")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    try:
        delete_storage_file(abs_path)
        flash("File eliminato correttamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    parent_subdir = os.path.dirname(filename)
    return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id, subdir=parent_subdir or None))


@bp.route("/clienti/<int:cliente_id>/cartella/elimina-cartella/<path:dirname>", methods=["POST"])
@role_required("admin", "operatore")
def cliente_cartella_delete_folder(cliente_id, dirname):
    cliente = Cliente.query.get_or_404(cliente_id)
    if not cliente.folder_path:
        flash("Nessuna cartella creata per questo cliente.", "warning")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    rel_path = os.path.join(cliente.folder_path, dirname).replace("\\", "/")
    abs_path = safe_path(rel_path)
    if not abs_path:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    home_abs = safe_path(cliente.folder_path)
    if abs_path == home_abs:
        flash("Impossibile eliminare la cartella principale.", "danger")
        return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id))

    try:
        delete_empty_storage_folder(abs_path)
        flash("Cartella eliminata correttamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    parent_subdir = os.path.dirname(dirname)
    return redirect(url_for("clienti.cliente_cartella", cliente_id=cliente.id, subdir=parent_subdir or None))


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
