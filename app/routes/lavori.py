import os
import shutil
from datetime import datetime

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from ..auth import login_required, role_required
from ..extensions import db
from ..models import CalendarEvent, Cliente, EmailLog, EmailMessage, FinancialMovement, Lavoro, Moodboard, Preventivo, Task
from ..storage_utils import build_breadcrumb, create_subfolder, get_lavoro_relative_path, list_entries, normalize_subdir, rename_storage_entry, resolve_collision, safe_path, save_uploaded_storage_file, slugify, ensure_storage_dir


bp = Blueprint("lavori", __name__)

UPLOAD_SUBDIR = "uploads/lavori_preventivi"
ALLOWED_PDF_EXTENSIONS = {".pdf"}


def ensure_upload_dir():
    path = os.path.join(current_app.static_folder, UPLOAD_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def save_preventivo_pdf(lavoro_id):
    file = request.files.get("preventivo_pdf")
    if not file or not file.filename:
        return None

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_PDF_EXTENSIONS:
        raise ValueError("Il file caricato non è un PDF. Sono accettati solo file con estensione .pdf.")

    ensure_upload_dir()
    safe_name = secure_filename(file.filename)
    storage_name = f"{lavoro_id}_{int(datetime.utcnow().timestamp())}_{safe_name}"
    rel_path = os.path.join(UPLOAD_SUBDIR, storage_name)
    abs_path = os.path.join(current_app.static_folder, rel_path)
    file.save(abs_path)
    return rel_path.replace("\\", "/")

status_lavori = ["Completato", "In corso", "In attesa", "Da iniziare"]


def parse_optional_float(value):
    if value in (None, ""):
        return 0
    return float(str(value).replace(",", "."))


def parse_optional_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_optional_id(value):
    if value in (None, ""):
        return None
    return int(value)


def apply_lavoro_form(lavoro):
    lavoro.descrizione = (request.form.get("descrizione") or "").strip()
    lavoro.cliente_id = parse_optional_id(request.form.get("cliente_id"))
    lavoro.priorita = request.form.get("priorita") or None
    lavoro.stato = request.form.get("stato") or None
    lavoro.data_inizio = parse_optional_date(request.form.get("data_inizio"))
    lavoro.data_fine = parse_optional_date(request.form.get("data_fine"))
    lavoro.data_pagamento = parse_optional_date(request.form.get("data_pagamento"))
    lavoro.preventivato = parse_optional_float(request.form.get("preventivato"))
    lavoro.note = (request.form.get("note") or "").strip() or None

    if not lavoro.descrizione:
        raise ValueError("La descrizione lavoro e obbligatoria.")
    if not lavoro.cliente_id:
        raise ValueError("Il cliente e obbligatorio.")
    if lavoro.stato not in status_lavori:
        raise ValueError("Stato lavoro non valido.")


@bp.route("/lavori/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def nuovo_lavoro():
    if request.method == "POST":
        descrizione = (request.form.get("descrizione") or "").strip()
        data_inizio = request.form.get("data_inizio")
        data_fine = request.form.get("data_fine")
        data_pagamento = request.form.get("data_pagamento")
        cliente_id = parse_optional_id(request.form.get("cliente_id"))
        priorita = (request.form.get("priorita") or "").strip().lower() or None
        stato = (request.form.get("stato") or "").strip() or None
        preventivato = parse_optional_float(request.form.get("preventivato"))
        note = (request.form.get("note") or "").strip() or None

        def convertToDate(data_string):
            if data_string:
                return datetime.strptime(data_string, "%Y-%m-%d").date()
            return None

        data_inizio_obj = convertToDate(data_inizio)
        data_fine_obj = convertToDate(data_fine)
        data_pagamento_obj = convertToDate(data_pagamento)

        if not descrizione:
            return jsonify({"success": False, "error": "La descrizione lavoro e obbligatoria."}), 400
        if not cliente_id:
            return jsonify({"success": False, "error": "Il cliente e obbligatorio."}), 400
        if stato not in status_lavori:
            return jsonify({"success": False, "error": "Stato lavoro non valido."}), 400

        nuovo_lavoro = Lavoro(
            descrizione=descrizione,
            data_inizio=data_inizio_obj,
            data_fine=data_fine_obj,
            data_pagamento=data_pagamento_obj,
            cliente_id=cliente_id,
            priorita=priorita,
            stato=stato,
            preventivato=preventivato,
            note=note,
        )
        db.session.add(nuovo_lavoro)
        db.session.commit()

        try:
            pdf_path = save_preventivo_pdf(nuovo_lavoro.id)
            if pdf_path:
                nuovo_lavoro.preventivo_pdf_path = pdf_path
                db.session.commit()
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
            return (
                jsonify(
                    {
                        "message": "Lavoro aggiunto con successo!",
                        "data": {
                            "descrizione": descrizione,
                            "data_inizio": (
                                data_inizio_obj.strftime("%d/%m/%Y")
                                if data_inizio_obj
                                else None
                            ),
                            "data_fine": (
                                data_fine_obj.strftime("%d/%m/%Y")
                                if data_fine_obj
                                else None
                            ),
                            "data_pagamento": (
                                data_pagamento_obj.strftime("%d/%m/%Y")
                                if data_pagamento_obj
                                else None
                            ),
                            "cliente_id": cliente_id,
                            "priorita": priorita,
                            "stato": stato,
                            "preventivato": preventivato,
                            "note": note,
                        },
                    }
                ),
                201,
            )

        return redirect(url_for("lavori.lavoro_page", lavoro_id=nuovo_lavoro.id))

    if request.method == "GET":
        clienti_list = Cliente.query.all()
        selected_cliente_id = request.args.get("cliente_id", type=int)
        return render_template(
            "lavoro_new.html",
            clienti=clienti_list,
            selected_cliente_id=selected_cliente_id,
        )


@bp.route("/lavori")
@login_required
def lavori():
    lavori_list = Lavoro.query.all()
    return render_template("lavori.html", lavori=lavori_list)


@bp.get("/lavori/<int:lavoro_id>")
@login_required
def lavoro_page(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    tasks = (
        Task.query.filter_by(lavoro_id=lavoro_id)
        .order_by(Task.updated_at.desc(), Task.created_at.desc())
        .limit(10)
        .all()
    )
    legacy_tasks = (
        sorted(lavoro.tasks, key=lambda task: task.timestamp or datetime.min, reverse=True)[:10]
        if lavoro.tasks
        else []
    )
    preventivi = (
        Preventivo.query.filter_by(lavoro_id=lavoro_id)
        .order_by(Preventivo.data_creazione.desc())
        .limit(10)
        .all()
    )
    eventi = (
        CalendarEvent.query.filter_by(lavoro_id=lavoro_id)
        .order_by(CalendarEvent.start_datetime.desc())
        .limit(10)
        .all()
    )
    movimenti = (
        FinancialMovement.query.filter_by(lavoro_id=lavoro_id)
        .order_by(FinancialMovement.movement_date.desc(), FinancialMovement.id.desc())
        .limit(10)
        .all()
    )

    quick_params = {"lavoro_id": lavoro.id}
    if lavoro.cliente_id:
        quick_params["cliente_id"] = lavoro.cliente_id
    quick_actions = {
        "nuovo_task": url_for("tasks.task_new", **quick_params),
        "nuovo_preventivo": url_for("nuovo_preventivo", **quick_params),
        "nuovo_evento": url_for("calendar.calendar_new", **quick_params),
        "nuovo_movimento": url_for("finance.finance_new", **quick_params),
        "modifica": url_for("lavori.lavoro_edit", lavoro_id=lavoro.id),
        "cliente": (
            url_for("cliente_page", cliente_id=lavoro.cliente_id)
            if lavoro.cliente_id
            else None
        ),
    }

    return render_template(
        "lavoro.html",
        lavoro=lavoro,
        tasks=tasks,
        legacy_tasks=legacy_tasks,
        preventivi=preventivi,
        eventi=eventi,
        movimenti=movimenti,
        quick_actions=quick_actions,
    )


@bp.route("/lavori/<int:lavoro_id>/edit", methods=["GET", "POST"])
@role_required("admin", "operatore")
def lavoro_edit(lavoro_id):
    # NOTA: folder_path NON viene aggiornato al cambio descrizione.
    # Il path su disco resta stabile per evitare rottura percorsi esterni/sync.
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    clienti_list = Cliente.query.order_by(Cliente.name.asc()).all()
    error = None

    if request.method == "POST":
        try:
            apply_lavoro_form(lavoro)

            if request.form.get("remove_pdf") == "1" and lavoro.preventivo_pdf_path:
                old_path = os.path.join(current_app.static_folder, lavoro.preventivo_pdf_path)
                if os.path.exists(old_path):
                    os.remove(old_path)
                lavoro.preventivo_pdf_path = None

            db.session.commit()

            pdf_path = save_preventivo_pdf(lavoro.id)
            if pdf_path:
                if lavoro.preventivo_pdf_path:
                    old_path = os.path.join(current_app.static_folder, lavoro.preventivo_pdf_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                lavoro.preventivo_pdf_path = pdf_path
                db.session.commit()

            return redirect(url_for("lavori.lavoro_page", lavoro_id=lavoro.id))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "lavoro_edit.html",
        lavoro=lavoro,
        clienti=clienti_list,
        status_lavori=status_lavori,
        error=error,
        form_action=url_for("lavori.lavoro_edit", lavoro_id=lavoro.id),
        page_title="Modifica lavoro",
        submit_label="Salva modifiche",
    )


@bp.post("/lavori/<int:lavoro_id>/remove-pdf")
@role_required("admin", "operatore")
def lavoro_remove_pdf(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    if lavoro.preventivo_pdf_path:
        old_path = os.path.join(current_app.static_folder, lavoro.preventivo_pdf_path)
        if os.path.exists(old_path):
            os.remove(old_path)
        lavoro.preventivo_pdf_path = None
        db.session.commit()
        flash("PDF preventivo rimosso.", "success")
    return redirect(url_for("lavori.lavoro_edit", lavoro_id=lavoro.id))


@bp.post("/lavori/<int:lavoro_id>/delete")
@role_required("admin", "operatore")
def lavoro_delete(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    lavoro_descrizione = lavoro.descrizione

    blocco = []
    n_preventivi = Preventivo.query.filter_by(lavoro_id=lavoro_id).count()
    if n_preventivi:
        blocco.append(f"{n_preventivi} preventiv{'i' if n_preventivi > 1 else 'o'}")
    n_finance = FinancialMovement.query.filter_by(lavoro_id=lavoro_id).count()
    if n_finance:
        blocco.append(f"{n_finance} moviment{'i finanziari' if n_finance > 1 else 'o finanziario'}")
    n_emaillog = EmailLog.query.filter_by(lavoro_id=lavoro_id).count()
    if n_emaillog:
        blocco.append(f"{n_emaillog} email log")
    n_emailmsg = EmailMessage.query.filter_by(lavoro_id=lavoro_id).count()
    if n_emailmsg:
        blocco.append(f"{n_emailmsg} messagg{'i' if n_emailmsg > 1 else 'gio'} email")

    if blocco:
        flash("Impossibile eliminare il lavoro: presenti " + ", ".join(blocco) + " collegati.", "danger")
        return redirect(url_for("lavori.lavoro_page", lavoro_id=lavoro_id))

    for evt in CalendarEvent.query.filter_by(lavoro_id=lavoro_id).all():
        db.session.delete(evt)
    for mb in Moodboard.query.filter_by(lavoro_id=lavoro_id).all():
        db.session.delete(mb)
    task_ids = [t.id for t in Task.query.filter_by(lavoro_id=lavoro_id).all()]
    if task_ids:
        CalendarEvent.query.filter(CalendarEvent.task_id.in_(task_ids)).update(
            {CalendarEvent.task_id: None}, synchronize_session=False
        )
        EmailLog.query.filter(EmailLog.task_id.in_(task_ids)).update(
            {EmailLog.task_id: None}, synchronize_session=False
        )
    for task in Task.query.filter_by(lavoro_id=lavoro_id).all():
        db.session.delete(task)

    if lavoro.preventivo_pdf_path:
        pdf_path = os.path.join(current_app.static_folder, lavoro.preventivo_pdf_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    if lavoro.folder_path:
        abs_path = safe_path(lavoro.folder_path)
        if abs_path and os.path.exists(abs_path):
            try:
                shutil.rmtree(abs_path)
            except OSError as e:
                flash(f"Impossibile eliminare la cartella: {str(e)}", "danger")
                return redirect(url_for("lavori.lavoro_page", lavoro_id=lavoro.id))

    db.session.delete(lavoro)
    db.session.commit()
    flash(f"Lavoro '{lavoro_descrizione}' eliminato con successo.", "success")
    return redirect(url_for("lavori.lavori"))


@bp.patch("/lavori/<int:lavoro_id>")
@role_required("admin", "operatore")
def status_lavoro_update(lavoro_id):
    lavoro = Lavoro.query.filter_by(id=lavoro_id).first()
    data = request.get_json()
    new_status = data["new_status"]
    if new_status not in status_lavori:
        db.session.rollback()
        return jsonify({"error": "Stato lavoro non valido."}), 400
    lavoro.stato = new_status
    db.session.commit()
    return jsonify(
        {
            "lavoro_id": lavoro.id,
            "lavoro_descrizione": lavoro.descrizione,
            "cliente": lavoro.cliente.name if lavoro.cliente else None,
            "nuovo_stato": new_status,
        }
    )


@bp.route("/lavori/<int:lavoro_id>/cartella/crea", methods=["POST"])
@role_required("admin", "operatore")
def lavoro_cartella_crea(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)

    wants_json = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
    )

    if lavoro.folder_path:
        if wants_json:
            return jsonify({"messaggio": "Cartella gia esistente.", "folder_path": lavoro.folder_path}), 200
        flash("Cartella gia esistente.", "warning")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    try:
        slug = slugify(lavoro.descrizione) or f"lavoro-{lavoro.id}"
        rel_path = get_lavoro_relative_path(lavoro.id, slug)
        rel_path = resolve_collision(rel_path)
        ensure_storage_dir(rel_path)
    except (OSError, IOError) as e:
        if wants_json:
            return jsonify({"error": f"Errore filesystem: {str(e)}"}), 500
        flash(f"Errore nella creazione della cartella: {str(e)}", "danger")
        return redirect(url_for("lavoro_page", lavoro_id=lavoro.id))

    lavoro.folder_path = rel_path
    db.session.commit()

    if wants_json:
        return jsonify({"messaggio": "Cartella lavoro creata correttamente.", "folder_path": rel_path}), 201

    flash("Cartella lavoro creata correttamente.", "success")
    return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))


@bp.route("/lavori/<int:lavoro_id>/cartella")
@login_required
def lavoro_cartella(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    folder_active = bool(lavoro.folder_path)
    subdir = normalize_subdir(request.args.get("subdir", ""))

    if subdir is None:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    if folder_active and subdir:
        rel_path = os.path.join(lavoro.folder_path, subdir).replace("\\", "/")
        abs_path = safe_path(rel_path)
        if not abs_path or not os.path.isdir(abs_path):
            flash("Cartella non trovata.", "warning")
            return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))
    elif folder_active:
        abs_path = safe_path(lavoro.folder_path)
    else:
        abs_path = None

    entries = list_entries(abs_path) if abs_path else []
    breadcrumb = build_breadcrumb(
        subdir,
        lambda **kw: url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id, **kw),
        "Cartella lavoro",
    )

    return render_template(
        "lavoro_cartella.html",
        lavoro=lavoro,
        entries=entries,
        folder_active=folder_active,
        subdir=subdir,
        breadcrumb=breadcrumb,
    )


@bp.route("/lavori/<int:lavoro_id>/cartella/upload", methods=["POST"])
@role_required("admin", "operatore")
def lavoro_cartella_upload(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    if not lavoro.folder_path:
        flash("Nessuna cartella creata per questo lavoro.", "warning")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    subdir = normalize_subdir(request.args.get("subdir", ""))
    if subdir is None:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    rel_path = os.path.join(lavoro.folder_path, subdir).replace("\\", "/") if subdir else lavoro.folder_path
    abs_path = safe_path(rel_path)
    if not abs_path or not os.path.isdir(abs_path):
        flash("Cartella non trovata.", "warning")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    file = request.files.get("file")
    if not file or not file.filename:
        flash("Nessun file selezionato.", "warning")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id, subdir=subdir or None))

    try:
        save_uploaded_storage_file(file, abs_path)
        flash("File caricato correttamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id, subdir=subdir or None))


@bp.route("/lavori/<int:lavoro_id>/cartella/sottocartella/crea", methods=["POST"])
@role_required("admin", "operatore")
def lavoro_cartella_sottocartella_crea(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    if not lavoro.folder_path:
        flash("Nessuna cartella creata per questo lavoro.", "warning")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    subdir = normalize_subdir(request.args.get("subdir", ""))
    if subdir is None:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    rel_path = os.path.join(lavoro.folder_path, subdir).replace("\\", "/") if subdir else lavoro.folder_path
    abs_path = safe_path(rel_path)
    if not abs_path or not os.path.isdir(abs_path):
        flash("Cartella non trovata.", "warning")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    folder_name = request.form.get("nome_cartella", "")
    try:
        create_subfolder(abs_path, folder_name)
        flash("Cartella creata correttamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id, subdir=subdir or None))


@bp.route("/lavori/<int:lavoro_id>/cartella/rinomina", methods=["POST"])
@role_required("admin", "operatore")
def lavoro_cartella_rename(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    if not lavoro.folder_path:
        flash("Nessuna cartella creata per questo lavoro.", "warning")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    subdir = normalize_subdir(request.args.get("subdir", ""))
    if subdir is None:
        flash("Percorso non valido.", "danger")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    rel_path = os.path.join(lavoro.folder_path, subdir).replace("\\", "/") if subdir else lavoro.folder_path
    abs_path = safe_path(rel_path)
    if not abs_path or not os.path.isdir(abs_path):
        flash("Cartella non trovata.", "warning")
        return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id))

    old_name = request.form.get("old_name", "").strip()
    new_name = request.form.get("new_name", "").strip()

    is_file = os.path.isfile(os.path.join(abs_path, old_name)) if old_name else False
    try:
        rename_storage_entry(abs_path, old_name, new_name)
        flash("File rinominato correttamente." if is_file else "Cartella rinominata correttamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("lavori.lavoro_cartella", lavoro_id=lavoro.id, subdir=subdir or None))


@bp.route("/lavori/<int:lavoro_id>/cartella/download/<path:filename>")
@login_required
def lavoro_cartella_download(lavoro_id, filename):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    if not lavoro.folder_path:
        return jsonify({"error": "Cartella non esistente."}), 404

    rel_path = os.path.join(lavoro.folder_path, filename).replace("\\", "/")
    abs_path = safe_path(rel_path)
    if not abs_path or not os.path.isfile(abs_path):
        return jsonify({"error": "File non trovato."}), 404

    download_name = os.path.basename(filename)
    return send_file(abs_path, as_attachment=True, download_name=download_name)
