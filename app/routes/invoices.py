import os
from datetime import date
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from ..auth import login_required, role_required
from ..extensions import db
from ..finance_service import sync_movement_from_received_invoice, sync_movement_from_sent_invoice
from ..models import Cliente, Fattura, FinancialMovement, Lavoro
from ..utils.parsing import parse_optional_date, parse_optional_id


bp = Blueprint("invoices", __name__)

INVOICE_STORAGE = "uploads/invoices"
ALLOWED_EXTENSIONS = {"pdf"}
PER_PAGE = 10


def invoice_form_choices():
    return {
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "lavori": Lavoro.query.order_by(Lavoro.descrizione.asc()).all(),
    }


def extension(filename):
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def save_invoice_pdf(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    ext = extension(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Formato file non valido. Carica un PDF.")
    storage_root = current_app.config["ERP_STORAGE_ROOT"]
    upload_dir = os.path.join(storage_root, INVOICE_STORAGE)
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = secure_filename(file_storage.filename)
    filename = f"{uuid4().hex}_{safe_name}"
    file_storage.save(os.path.join(upload_dir, filename))
    return f"{INVOICE_STORAGE}/{filename}"


def delete_invoice_pdf(pdf_path):
    if not pdf_path:
        return
    storage_root = current_app.config["ERP_STORAGE_ROOT"]
    full_path = os.path.join(storage_root, pdf_path)
    if os.path.isfile(full_path):
        try:
            os.remove(full_path)
        except OSError:
            current_app.logger.exception("Errore rimozione PDF fattura: %s", full_path)


def apply_invoice_form(fattura):
    fattura.invoice_type = (request.form.get("invoice_type") or "sent")
    fattura.numero = (request.form.get("numero") or "").strip()
    fattura.data_emissione = parse_optional_date(request.form.get("data_emissione"))
    fattura.data_scadenza = parse_optional_date(request.form.get("data_scadenza"))
    fattura.importo = float(request.form.get("importo") or 0)
    fattura.aliquota_iva = int(request.form.get("aliquota_iva") or 22)
    fattura.data_pagamento = parse_optional_date(request.form.get("data_pagamento"))
    fattura.note = (request.form.get("note") or "").strip() or None

    if fattura.invoice_type == "sent":
        fattura.cliente_id = parse_optional_id(request.form.get("cliente_id"))
        fattura.lavoro_id = parse_optional_id(request.form.get("lavoro_id"))
        fattura.pagato = request.form.get("pagato") == "on"
        fattura.fornitore = None
        fattura.stato_pagamento = None
    else:
        fattura.cliente_id = None
        fattura.lavoro_id = None
        fattura.pagato = False
        fattura.fornitore = (request.form.get("fornitore") or "").strip() or None
        fattura.stato_pagamento = (request.form.get("stato_pagamento") or "da_pagare")

    if not fattura.numero:
        raise ValueError("Il numero fattura e obbligatorio.")
    if fattura.invoice_type == "sent" and not fattura.cliente_id:
        raise ValueError("Il cliente e obbligatorio.")
    if fattura.invoice_type == "received" and not fattura.fornitore:
        raise ValueError("Il fornitore e obbligatorio.")
    if not fattura.data_emissione:
        raise ValueError("La data emissione e obbligatoria.")
    if fattura.importo <= 0:
        raise ValueError("L'importo deve essere maggiore di zero.")


@bp.get("/invoices")
@login_required
def invoices_index():
    sent_page = request.args.get("sent_page", 1, type=int)
    received_page = request.args.get("received_page", 1, type=int)

    sent_query = Fattura.query.filter_by(invoice_type="sent").order_by(
        Fattura.data_emissione.desc(), Fattura.id.desc()
    )
    received_query = Fattura.query.filter_by(invoice_type="received").order_by(
        Fattura.data_emissione.desc(), Fattura.id.desc()
    )

    sent_pagination = sent_query.paginate(page=sent_page, per_page=PER_PAGE, error_out=False)
    received_pagination = received_query.paginate(page=received_page, per_page=PER_PAGE, error_out=False)

    received_ids = [f.id for f in received_pagination.items]
    sent_ids = [f.id for f in sent_pagination.items]
    linked_movement_ids = set()
    if received_ids:
        rows = FinancialMovement.query.with_entities(
            FinancialMovement.source_id
        ).filter(
            FinancialMovement.source_type == "received_invoice",
            FinancialMovement.source_id.in_(received_ids),
        ).all()
        linked_movement_ids.update(r[0] for r in rows)
    if sent_ids:
        rows = FinancialMovement.query.with_entities(
            FinancialMovement.source_id
        ).filter(
            FinancialMovement.source_type == "sent_invoice",
            FinancialMovement.source_id.in_(sent_ids),
        ).all()
        linked_movement_ids.update(r[0] for r in rows)

    return render_template(
        "invoices.html",
        sent_pagination=sent_pagination,
        received_pagination=received_pagination,
        linked_movement_ids=linked_movement_ids,
        **invoice_form_choices(),
    )


@bp.route("/invoices/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def invoice_new():
    cliente_id = request.args.get("cliente_id", type=int)
    lavoro_id = request.args.get("lavoro_id", type=int)
    invoice_type = request.args.get("type") or "sent"
    fattura = Fattura(
        invoice_type=invoice_type,
        cliente_id=cliente_id if invoice_type == "sent" else None,
        lavoro_id=lavoro_id if invoice_type == "sent" else None,
        data_emissione=date.today(),
    )
    error = None

    if request.method == "POST":
        file = request.files.get("pdf")
        try:
            apply_invoice_form(fattura)
            if file and file.filename:
                fattura.pdf_path = save_invoice_pdf(file)
            db.session.add(fattura)
            db.session.flush()
            if fattura.invoice_type == "received":
                sync_movement_from_received_invoice(fattura)
            elif fattura.invoice_type == "sent":
                sync_movement_from_sent_invoice(fattura)
            db.session.commit()
            flash("Fattura creata con successo.", "success")
            return redirect(url_for("invoices.invoices_index"))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "invoice_form.html",
        fattura=fattura,
        error=error,
        form_action=url_for("invoices.invoice_new"),
        page_title="Nuova fattura",
        submit_label="Crea fattura",
        **invoice_form_choices(),
    )


@bp.route("/invoices/<int:invoice_id>/edit", methods=["GET", "POST"])
@role_required("admin", "operatore")
def invoice_edit(invoice_id):
    fattura = Fattura.query.get_or_404(invoice_id)
    error = None

    if request.method == "POST":
        file = request.files.get("pdf")
        old_pdf = fattura.pdf_path
        try:
            apply_invoice_form(fattura)
            if file and file.filename:
                if old_pdf:
                    delete_invoice_pdf(old_pdf)
                fattura.pdf_path = save_invoice_pdf(file)
            db.session.flush()
            if fattura.invoice_type == "received":
                sync_movement_from_received_invoice(fattura)
            elif fattura.invoice_type == "sent":
                sync_movement_from_sent_invoice(fattura)
            db.session.commit()
            flash("Fattura aggiornata con successo.", "success")
            return redirect(url_for("invoices.invoices_index"))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "invoice_form.html",
        fattura=fattura,
        error=error,
        form_action=url_for("invoices.invoice_edit", invoice_id=fattura.id),
        page_title="Modifica fattura",
        submit_label="Salva modifiche",
        **invoice_form_choices(),
    )


@bp.post("/invoices/<int:invoice_id>/delete")
@role_required("admin", "operatore")
def invoice_delete(invoice_id):
    fattura = Fattura.query.get_or_404(invoice_id)
    try:
        linked = FinancialMovement.query.filter(
            FinancialMovement.source_id == fattura.id,
            FinancialMovement.source_type.in_(["received_invoice", "sent_invoice"]),
        ).first()
        if linked:
            db.session.delete(linked)
        delete_invoice_pdf(fattura.pdf_path)
        db.session.delete(fattura)
        db.session.commit()
        flash("Fattura eliminata con successo.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore eliminazione fattura %d", invoice_id)
        flash("Impossibile eliminare la fattura. Operazione annullata.", "danger")
    return redirect(url_for("invoices.invoices_index"))


@bp.get("/invoices/<int:invoice_id>/pdf")
@login_required
def invoice_pdf(invoice_id):
    fattura = Fattura.query.get_or_404(invoice_id)
    if not fattura.pdf_path:
        flash("Nessun PDF allegato a questa fattura.", "warning")
        return redirect(url_for("invoices.invoices_index"))
    storage_root = current_app.config["ERP_STORAGE_ROOT"]
    directory = os.path.dirname(os.path.join(storage_root, fattura.pdf_path))
    filename = os.path.basename(fattura.pdf_path)
    return send_from_directory(directory, filename)
