import os
from uuid import uuid4

from PIL import Image

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from ..auth import login_required, role_required
from ..extensions import db
from ..models import (
    Cliente,
    Lavoro,
    Moodboard,
    MoodboardImage,
    Task,
    User,
)
from ..utils.parsing import parse_optional_id


bp = Blueprint("moodboards", __name__)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
UPLOAD_FOLDER = "uploads/moodboards"


def validate_extension(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not validate_extension(file_storage.filename):
        raise ValueError("Formato immagine non valido. Usa JPG, PNG o WEBP.")
    upload_root = os.path.join(current_app.static_folder, UPLOAD_FOLDER)
    os.makedirs(upload_root, exist_ok=True)
    safe_name = secure_filename(file_storage.filename)
    filename = f"{uuid4().hex}_{safe_name}"
    file_path = os.path.join(upload_root, filename)

    max_dim = current_app.config.get("MAX_IMAGE_DIMENSION", 1920)
    quality = current_app.config.get("MAX_IMAGE_QUALITY", 85)

    extension = filename.rsplit(".", 1)[1].lower()
    fmt_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
    save_kwargs = {"JPEG": {"quality": quality, "optimize": True}, "PNG": {"optimize": True}, "WEBP": {"quality": quality}}
    fmt = fmt_map[extension]

    file_storage.seek(0)
    img = Image.open(file_storage)

    if extension in ("jpg", "jpeg") and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    if max(img.width, img.height) > max_dim:
        ratio = max_dim / max(img.width, img.height)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

    img.save(file_path, fmt, **save_kwargs.get(fmt, {}))
    return f"{UPLOAD_FOLDER}/{filename}"


def moodboard_form_choices():
    return {
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "lavori": Lavoro.query.order_by(Lavoro.descrizione.asc()).all(),
        "tasks": Task.query.order_by(Task.created_at.desc()).all(),
    }


@bp.get("/moodboards")
@login_required
def moodboard_index():
    moodboards = (
        Moodboard.query
        .order_by(Moodboard.updated_at.desc())
        .all()
    )
    return render_template(
        "moodboards.html",
        moodboards=moodboards,
        **moodboard_form_choices(),
    )


@bp.get("/moodboards/<int:id>")
@login_required
def moodboard_detail(id):
    moodboard = Moodboard.query.get_or_404(id)
    images = moodboard.images
    return render_template(
        "moodboard_detail.html",
        moodboard=moodboard,
        images=images,
        **moodboard_form_choices(),
    )


@bp.route("/moodboards/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def moodboard_new():
    task_id = request.args.get("task_id", type=int)
    task = Task.query.get(task_id) if task_id else None
    cliente_id = None
    lavoro_id = None
    if task:
        cliente_id = task.cliente_id
        lavoro_id = task.lavoro_id

    moodboard = Moodboard(
        task_id=task_id,
        cliente_id=cliente_id,
        lavoro_id=lavoro_id,
    )
    error = None

    if request.method == "POST":
        moodboard.title = (request.form.get("title") or "").strip()
        moodboard.description = (request.form.get("description") or "").strip() or None
        moodboard.task_id = parse_optional_id(request.form.get("task_id"))
        moodboard.cliente_id = parse_optional_id(request.form.get("cliente_id"))
        moodboard.lavoro_id = parse_optional_id(request.form.get("lavoro_id"))
        moodboard.created_by = g.get("current_user").id if g.get("current_user") else None

        if moodboard.task_id:
            linked_task = db.session.get(Task, moodboard.task_id)
            if linked_task:
                if not moodboard.cliente_id:
                    moodboard.cliente_id = linked_task.cliente_id
                if not moodboard.lavoro_id:
                    moodboard.lavoro_id = linked_task.lavoro_id

        if not moodboard.title:
            error = "Il titolo e obbligatorio."
        else:
            try:
                db.session.add(moodboard)
                db.session.commit()
                return redirect(url_for("moodboards.moodboard_detail", id=moodboard.id))
            except Exception as exc:
                db.session.rollback()
                error = str(exc)

    return render_template(
        "moodboard_form.html",
        moodboard=moodboard,
        error=error,
        form_action=url_for("moodboards.moodboard_new"),
        page_title="Nuova moodboard",
        submit_label="Crea moodboard",
        **moodboard_form_choices(),
    )


@bp.route("/moodboards/<int:id>/edit", methods=["GET", "POST"])
@role_required("admin", "operatore")
def moodboard_edit(id):
    moodboard = Moodboard.query.get_or_404(id)
    error = None

    if request.method == "POST":
        moodboard.title = (request.form.get("title") or "").strip()
        moodboard.description = (request.form.get("description") or "").strip() or None
        moodboard.task_id = parse_optional_id(request.form.get("task_id"))
        moodboard.cliente_id = parse_optional_id(request.form.get("cliente_id"))
        moodboard.lavoro_id = parse_optional_id(request.form.get("lavoro_id"))

        if moodboard.task_id:
            linked_task = db.session.get(Task, moodboard.task_id)
            if linked_task:
                if not moodboard.cliente_id:
                    moodboard.cliente_id = linked_task.cliente_id
                if not moodboard.lavoro_id:
                    moodboard.lavoro_id = linked_task.lavoro_id

        if not moodboard.title:
            error = "Il titolo e obbligatorio."
        else:
            try:
                db.session.commit()
                return redirect(url_for("moodboards.moodboard_detail", id=moodboard.id))
            except Exception as exc:
                db.session.rollback()
                error = str(exc)

    return render_template(
        "moodboard_form.html",
        moodboard=moodboard,
        error=error,
        form_action=url_for("moodboards.moodboard_edit", id=moodboard.id),
        page_title="Modifica moodboard",
        submit_label="Salva modifiche",
        **moodboard_form_choices(),
    )


@bp.post("/moodboards/<int:id>/delete")
@role_required("admin", "operatore")
def moodboard_delete(id):
    moodboard = Moodboard.query.get_or_404(id)
    try:
        for image in moodboard.images:
            if image.image_path:
                delete_image_file(image.image_path)
        db.session.delete(moodboard)
        db.session.commit()
        flash("Moodboard eliminata con successo.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore eliminazione moodboard %d", id)
        flash("Impossibile eliminare la moodboard. Operazione annullata.", "danger")
    return redirect(url_for("moodboards.moodboard_index"))


@bp.post("/moodboards/<int:id>/images")
@role_required("admin", "operatore")
def moodboard_add_image(id):
    moodboard = Moodboard.query.get_or_404(id)
    error = None

    source_type = request.form.get("source_type", "upload")
    title = (request.form.get("title") or "").strip() or None
    note = (request.form.get("note") or "").strip() or None
    source_url_input = (request.form.get("source_url") or "").strip() or None

    next_order = (
        db.session.query(
            db.func.coalesce(db.func.max(MoodboardImage.sort_order), -1)
        )
        .filter(MoodboardImage.moodboard_id == moodboard.id)
        .scalar()
    ) + 1

    image = MoodboardImage(
        moodboard_id=moodboard.id,
        title=title,
        sort_order=next_order,
        note=note,
        source_url=source_url_input,
    )

    if source_type == "url":
        image_url = (request.form.get("image_url") or "").strip()
        if not image_url:
            error = "Inserisci un URL immagine."
        elif not image_url.startswith(("http://", "https://")):
            error = "URL non valido."
        else:
            image.source_type = "url"
            image.image_url = image_url
    else:
        file_storage = request.files.get("image_file")
        if not file_storage or not file_storage.filename:
            error = "Seleziona un file immagine."
        else:
            try:
                path = save_upload(file_storage)
                if path:
                    image.source_type = "upload"
                    image.image_path = path
                else:
                    error = "Errore durante il salvataggio del file."
            except ValueError as exc:
                error = str(exc)

    if error:
        db.session.rollback()
        return redirect(url_for("moodboards.moodboard_detail", id=moodboard.id, _anchor="add-image-form"))

    db.session.add(image)
    db.session.commit()
    return redirect(url_for("moodboards.moodboard_detail", id=moodboard.id))


@bp.post("/moodboards/<int:id>/images/<int:image_id>/delete")
@role_required("admin", "operatore")
def moodboard_delete_image(id, image_id):
    moodboard = Moodboard.query.get_or_404(id)
    image = MoodboardImage.query.get_or_404(image_id)
    if image.moodboard_id != moodboard.id:
        return redirect(url_for("moodboards.moodboard_detail", id=moodboard.id))
    try:
        if image.image_path:
            delete_image_file(image.image_path)
        db.session.delete(image)
        db.session.commit()
        flash("Immagine rimossa dalla moodboard.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore eliminazione immagine moodboard %d", image_id)
        flash("Impossibile rimuovere l'immagine. Operazione annullata.", "danger")
    return redirect(url_for("moodboards.moodboard_detail", id=moodboard.id))


@bp.get("/tasks/<int:task_id>/moodboard")
@login_required
def task_moodboard(task_id):
    task = Task.query.get_or_404(task_id)
    moodboard = Moodboard.query.filter_by(task_id=task.id).first()
    if moodboard:
        return redirect(url_for("moodboards.moodboard_detail", id=moodboard.id))
    return redirect(url_for("moodboards.moodboard_new", task_id=task.id))


def delete_image_file(image_path):
    if not image_path:
        return
    upload_prefix = f"{UPLOAD_FOLDER}/"
    if not image_path.startswith(upload_prefix):
        return
    full_path = os.path.join(current_app.static_folder, image_path)
    if os.path.isfile(full_path):
        try:
            os.remove(full_path)
        except OSError:
            current_app.logger.exception("Errore rimozione file immagine moodboard: %s", full_path)
