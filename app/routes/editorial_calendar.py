from calendar import monthrange
from datetime import date, datetime, timedelta
import os
from uuid import uuid4

from flask import Blueprint, current_app, redirect, render_template, request, url_for
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from ..auth import login_required, role_required
from ..extensions import db
from ..models import (
    EDITORIAL_CLIENT_APPROVAL_STATUSES,
    EDITORIAL_CONTENT_TYPES,
    EDITORIAL_PLATFORMS,
    EDITORIAL_STATUSES,
    Cliente,
    EditorialPublication,
    EditorialPublicationImage,
    User,
)


bp = Blueprint("editorial_calendar", __name__)

MONTH_NAMES = (
    "",
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
)
ALLOWED_PREVIEW_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
PREVIEW_UPLOAD_FOLDER = "uploads/editorial_previews"


def parse_optional_id(value):
    if not value:
        return None
    return int(value)


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def month_bounds(year, month):
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    next_month = last_day + timedelta(days=1)
    return first_day, last_day, next_month


def adjacent_month_urls(cliente_id, year, month):
    first_day = date(year, month, 1)
    prev_day = first_day - timedelta(days=1)
    next_day = month_bounds(year, month)[2]
    return (
        url_for(
            "editorial_calendar.client_calendar",
            cliente_id=cliente_id,
            year=prev_day.year,
            month=prev_day.month,
        ),
        url_for(
            "editorial_calendar.client_calendar",
            cliente_id=cliente_id,
            year=next_day.year,
            month=next_day.month,
        ),
    )


def build_month_weeks(year, month, publications):
    first_day, last_day, _ = month_bounds(year, month)
    grid_start = first_day - timedelta(days=first_day.weekday())
    grid_end = last_day + timedelta(days=(6 - last_day.weekday()))
    publications_by_date = {}

    for publication in publications:
        publications_by_date.setdefault(publication.publication_date, []).append(publication)

    weeks = []
    current_day = grid_start
    while current_day <= grid_end:
        week = []
        for _ in range(7):
            day_publications = sorted(
                publications_by_date.get(current_day, []),
                key=lambda item: (
                    item.publication_date,
                    ",".join(item.get_platforms()),
                    item.content_type,
                    item.title,
                ),
            )
            week.append(
                {
                    "date": current_day,
                    "day": current_day.day,
                    "in_month": current_day.month == month,
                    "is_today": current_day == date.today(),
                    "publications": day_publications,
                }
            )
            current_day += timedelta(days=1)
        weeks.append(week)

    return weeks


def group_publications_by_day(publications):
    grouped = []
    current_date = None
    current_items = None

    for publication in publications:
        if publication.publication_date != current_date:
            current_date = publication.publication_date
            current_items = {"date": current_date, "publications": []}
            grouped.append(current_items)
        current_items["publications"].append(publication)

    return grouped


def editorial_form_choices():
    return {
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "users": User.query.order_by(User.name.asc(), User.email.asc()).all(),
        "platforms": EDITORIAL_PLATFORMS,
        "content_types": EDITORIAL_CONTENT_TYPES,
        "statuses": EDITORIAL_STATUSES,
        "client_approval_statuses": EDITORIAL_CLIENT_APPROVAL_STATUSES,
    }


def preview_extension(filename):
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def save_preview_file(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    extension = preview_extension(file_storage.filename)
    if extension not in ALLOWED_PREVIEW_EXTENSIONS:
        raise ValueError("Formato immagine non valido. Usa JPG, PNG o WEBP.")

    upload_root = os.path.join(current_app.static_folder, PREVIEW_UPLOAD_FOLDER)
    os.makedirs(upload_root, exist_ok=True)

    safe_name = secure_filename(file_storage.filename)
    filename = f"{uuid4().hex}_{safe_name}"
    file_storage.save(os.path.join(upload_root, filename))
    return f"{PREVIEW_UPLOAD_FOLDER}/{filename}"


def apply_editorial_form(publication):
    selected_platforms = request.form.getlist("platforms")
    invalid_platforms = [
        platform
        for platform in selected_platforms
        if platform not in EDITORIAL_PLATFORMS
    ]
    if not selected_platforms:
        raise ValueError("Seleziona almeno una piattaforma.")
    if invalid_platforms:
        raise ValueError("Piattaforma non valida.")

    publication.cliente_id = parse_optional_id(request.form.get("cliente_id"))
    publication.publication_date = parse_date(request.form.get("publication_date"))
    publication.set_platforms(selected_platforms)
    publication.content_type = request.form.get("content_type") or "post_grafico"
    publication.title = (request.form.get("title") or "").strip()
    publication.caption = (request.form.get("caption") or "").strip() or None
    publication.status = request.form.get("status") or "idea"
    publication.assigned_user_id = parse_optional_id(request.form.get("assigned_user_id"))
    publication.client_approval_status = (
        request.form.get("client_approval_status") or "da_approvare"
    )
    publication.internal_notes = (request.form.get("internal_notes") or "").strip() or None
    publication.asset_url = (request.form.get("asset_url") or "").strip() or None

    preview_path = save_preview_file(request.files.get("preview_image"))
    if preview_path:
        publication.preview_image_path = preview_path

    if request.form.get("remove_preview") == "1":
        publication.preview_image_path = None

    if not publication.cliente_id:
        raise ValueError("Il cliente e obbligatorio.")
    if publication.publication_date is None:
        raise ValueError("La data pubblicazione e obbligatoria.")
    if publication.content_type not in EDITORIAL_CONTENT_TYPES:
        raise ValueError("Tipo contenuto non valido.")
    if not publication.title:
        raise ValueError("Il tema/titolo interno e obbligatorio.")
    if publication.status not in EDITORIAL_STATUSES:
        raise ValueError("Stato pubblicazione non valido.")
    if publication.client_approval_status not in EDITORIAL_CLIENT_APPROVAL_STATUSES:
        raise ValueError("Stato approvazione cliente non valido.")


def apply_publication_filters(query):
    cliente_id = request.args.get("cliente_id", type=int)
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    platform = request.args.get("platform")
    status = request.args.get("status")
    assigned_user_id = request.args.get("assigned_user_id", type=int)

    if cliente_id:
        query = query.filter(EditorialPublication.cliente_id == cliente_id)
    if year and month and 1 <= month <= 12:
        first_day, last_day, _ = month_bounds(year, month)
        query = query.filter(EditorialPublication.publication_date >= first_day)
        query = query.filter(EditorialPublication.publication_date <= last_day)
    if platform in EDITORIAL_PLATFORMS:
        query = query.filter(
            or_(
                EditorialPublication.platforms == platform,
                EditorialPublication.platforms.like(f"{platform},%"),
                EditorialPublication.platforms.like(f"%,{platform},%"),
                EditorialPublication.platforms.like(f"%,{platform}"),
                EditorialPublication.platform == platform,
            )
        )
    if status in EDITORIAL_STATUSES:
        query = query.filter(EditorialPublication.status == status)
    if assigned_user_id:
        query = query.filter(EditorialPublication.assigned_user_id == assigned_user_id)

    return query


def current_filter_context(default_cliente_id=None, default_year=None, default_month=None):
    active_cliente_id = request.args.get("cliente_id", default_cliente_id, type=int)
    active_assigned_user_id = request.args.get("assigned_user_id", type=int)
    active_platform = request.args.get("platform")
    active_status = request.args.get("status")

    if active_platform not in EDITORIAL_PLATFORMS:
        active_platform = None
    if active_status not in EDITORIAL_STATUSES:
        active_status = None

    list_query_params = {}
    if active_cliente_id:
        list_query_params["cliente_id"] = active_cliente_id
    if default_year:
        list_query_params["year"] = default_year
    if default_month:
        list_query_params["month"] = default_month
    if active_platform:
        list_query_params["platform"] = active_platform
    if active_status:
        list_query_params["status"] = active_status
    if active_assigned_user_id:
        list_query_params["assigned_user_id"] = active_assigned_user_id

    calendar_query_params = {
        key: value
        for key, value in list_query_params.items()
        if key != "cliente_id"
    }

    return {
        "active_cliente_id": active_cliente_id,
        "active_assigned_user_id": active_assigned_user_id,
        "active_platform": active_platform,
        "active_status": active_status,
        "list_filter_params": list_query_params,
        "calendar_filter_params": calendar_query_params,
    }


@bp.get("/editorial-calendar")
@login_required
def editorial_index():
    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)
    if selected_month < 1 or selected_month > 12:
        selected_year = today.year
        selected_month = today.month

    publications = (
        apply_publication_filters(EditorialPublication.query)
        .order_by(EditorialPublication.publication_date.asc(), EditorialPublication.id.asc())
        .all()
    )
    filter_context = current_filter_context(
        default_year=selected_year,
        default_month=selected_month,
    )

    return render_template(
        "editorial_calendar.html",
        view_mode="list",
        publications=publications,
        grouped_publications=group_publications_by_day(publications),
        current_year=selected_year,
        current_month=selected_month,
        month_name=MONTH_NAMES[selected_month],
        months=enumerate(MONTH_NAMES),
        **filter_context,
        **editorial_form_choices(),
    )


def adjacent_month_padding(year, month):
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    grid_start = first_day - timedelta(days=first_day.weekday())
    grid_end = last_day + timedelta(days=(6 - last_day.weekday()))
    return grid_start, grid_end


@bp.get("/editorial-calendar/clienti/<int:cliente_id>")
@login_required
def client_calendar(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    today = date.today()
    current_year = request.args.get("year", today.year, type=int)
    current_month = request.args.get("month", today.month, type=int)

    if current_month < 1 or current_month > 12:
        current_year = today.year
        current_month = today.month

    grid_start, grid_end = adjacent_month_padding(current_year, current_month)
    publications = (
        EditorialPublication.query.filter_by(cliente_id=cliente.id)
        .filter(EditorialPublication.publication_date >= grid_start)
        .filter(EditorialPublication.publication_date <= grid_end)
        .order_by(EditorialPublication.publication_date.asc(), EditorialPublication.id.asc())
        .all()
    )
    weeks = build_month_weeks(current_year, current_month, publications)
    prev_month_url, next_month_url = adjacent_month_urls(
        cliente.id,
        current_year,
        current_month,
    )
    filter_context = current_filter_context(
        default_cliente_id=cliente.id,
        default_year=current_year,
        default_month=current_month,
    )

    return render_template(
        "editorial_calendar.html",
        view_mode="calendar",
        cliente=cliente,
        publications=publications,
        grouped_publications=group_publications_by_day(publications),
        weeks=weeks,
        current_year=current_year,
        current_month=current_month,
        month_name=MONTH_NAMES[current_month],
        prev_month_url=prev_month_url,
        next_month_url=next_month_url,
        months=enumerate(MONTH_NAMES),
        **filter_context,
        **editorial_form_choices(),
    )


@bp.route("/editorial-calendar/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def editorial_new():
    cliente_id = request.args.get("cliente_id", type=int)
    publication_date = parse_date(request.args.get("date")) or date.today()
    publication = EditorialPublication(
        cliente_id=cliente_id,
        publication_date=publication_date,
    )
    error = None
    form_data = {}
    form_platforms = []

    if request.method == "POST":
        for key in request.form.keys():
            vals = request.form.getlist(key)
            form_data[key] = vals if len(vals) != 1 else vals[0]
        form_platforms = request.form.getlist("platforms")
        try:
            apply_editorial_form(publication)
            db.session.add(publication)
            handle_publication_images(publication)
            db.session.commit()
            return redirect(
                url_for(
                    "editorial_calendar.client_calendar",
                    cliente_id=publication.cliente_id,
                    year=publication.publication_date.year,
                    month=publication.publication_date.month,
                )
            )
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "editorial_publication_form.html",
        publication=publication,
        error=error,
        form_data=form_data,
        form_platforms=form_platforms,
        form_action=url_for("editorial_calendar.editorial_new"),
        page_title="Nuova pubblicazione",
        submit_label="Crea pubblicazione",
        **editorial_form_choices(),
    )


def handle_publication_images(publication):
    """Handle additional image uploads and removals for a publication.
    Must be called after db.session.add(publication) and before commit."""
    if publication.id is None:
        db.session.flush()

    additional_files = request.files.getlist("additional_images")
    for file_storage in additional_files:
        path = save_preview_file(file_storage)
        if path:
            max_order = (
                db.session.query(
                    db.func.coalesce(db.func.max(EditorialPublicationImage.sort_order), -1)
                )
                .filter(EditorialPublicationImage.publication_id == publication.id)
                .scalar()
            )
            img = EditorialPublicationImage(
                publication_id=publication.id,
                image_path=path,
                sort_order=max_order + 1,
            )
            db.session.add(img)

    remove_ids = request.form.getlist("remove_image_ids")
    for rid in remove_ids:
        try:
            img = EditorialPublicationImage.query.get(int(rid))
            if img and img.publication_id == publication.id:
                db.session.delete(img)
        except (ValueError, TypeError):
            pass


@bp.route("/editorial-calendar/<int:publication_id>/edit", methods=["GET", "POST"])
@role_required("admin", "operatore")
def editorial_edit(publication_id):
    publication = EditorialPublication.query.get_or_404(publication_id)
    error = None
    form_data = {}
    form_platforms = []

    if request.method == "POST":
        for key in request.form.keys():
            vals = request.form.getlist(key)
            form_data[key] = vals if len(vals) != 1 else vals[0]
        form_platforms = request.form.getlist("platforms")
        try:
            apply_editorial_form(publication)
            handle_publication_images(publication)
            db.session.commit()
            return redirect(
                url_for(
                    "editorial_calendar.client_calendar",
                    cliente_id=publication.cliente_id,
                    year=publication.publication_date.year,
                    month=publication.publication_date.month,
                )
            )
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "editorial_publication_form.html",
        publication=publication,
        error=error,
        form_data=form_data,
        form_platforms=form_platforms,
        form_action=url_for(
            "editorial_calendar.editorial_edit",
            publication_id=publication.id,
        ),
        page_title="Modifica pubblicazione",
        submit_label="Salva modifiche",
        **editorial_form_choices(),
    )


@bp.post("/editorial-calendar/<int:publication_id>/delete")
@role_required("admin", "operatore")
def editorial_delete(publication_id):
    publication = EditorialPublication.query.get_or_404(publication_id)
    publication.status = "annullato"
    db.session.commit()
    return redirect(
        url_for(
            "editorial_calendar.client_calendar",
            cliente_id=publication.cliente_id,
            year=publication.publication_date.year,
            month=publication.publication_date.month,
        )
    )
