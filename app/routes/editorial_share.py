from calendar import monthrange
from datetime import date, timedelta

from flask import Blueprint, abort, g, render_template, request, url_for

from ..auth import role_required
from ..extensions import db
from ..models import (
    Cliente,
    EditorialPublication,
    EditorialShareLink,
)
from ..utils.calendar_helpers import MONTH_NAMES, month_navigation

bp = Blueprint("editorial_share", __name__)


def build_month_weeks(year, month, publications):
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    grid_start = first_day - timedelta(days=first_day.weekday())
    grid_end = last_day + timedelta(days=(6 - last_day.weekday()))

    publications_by_date = {}
    for p in publications:
        publications_by_date.setdefault(p.publication_date, []).append(p)

    weeks = []
    current_day = grid_start
    while current_day <= grid_end:
        week = []
        for _ in range(7):
            pubs = sorted(
                publications_by_date.get(current_day, []),
                key=lambda x: (x.publication_date, x.title),
            )
            week.append({
                "date": current_day,
                "day": current_day.day,
                "in_month": current_day.month == month,
                "is_today": current_day == date.today(),
                "publications": pubs,
            })
            current_day += timedelta(days=1)
        weeks.append(week)
    return weeks


@bp.route("/editorial-share/generate", methods=["POST"])
@role_required("admin", "operatore")
def generate():
    cliente_id = request.form.get("cliente_id", type=int)
    year = request.form.get("year", type=int)
    month = request.form.get("month", type=int)

    if not cliente_id or not year or not month:
        return {"error": "Parametri mancanti"}, 400
    if month < 1 or month > 12:
        return {"error": "Mese non valido"}, 400

    link = EditorialShareLink(
        cliente_id=cliente_id,
        year=year,
        month=month,
        created_by_id=g.current_user.id,
    )
    db.session.add(link)
    db.session.commit()

    share_url = url_for("editorial_share.view_shared", token=link.token, _external=True)
    return {"token": link.token, "url": share_url, "id": link.id}


@bp.get("/editorial-share/<token>")
def view_shared(token):
    link = EditorialShareLink.query.filter_by(token=str(token), is_active=True).first()
    if not link:
        abort(404)

    cliente = Cliente.query.get_or_404(link.cliente_id)
    today = date.today()
    year = request.args.get("year", link.year, type=int)
    month = request.args.get("month", link.month, type=int)
    if month < 1 or month > 12:
        year = link.year
        month = link.month

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    grid_start = first_day - timedelta(days=first_day.weekday())
    grid_end = last_day + timedelta(days=(6 - last_day.weekday()))

    publications = (
        EditorialPublication.query
        .filter_by(cliente_id=cliente.id)
        .filter(EditorialPublication.publication_date >= grid_start)
        .filter(EditorialPublication.publication_date <= grid_end)
        .order_by(EditorialPublication.publication_date.asc(), EditorialPublication.id.asc())
        .all()
    )

    weeks = build_month_weeks(year, month, publications)
    prev_year, prev_month, next_year, next_month = month_navigation(year, month)
    prev_month_url = url_for("editorial_share.view_shared", token=token, year=prev_year, month=prev_month)
    next_month_url = url_for("editorial_share.view_shared", token=token, year=next_year, month=next_month)

    return render_template(
        "editorial_shared_calendar.html",
        cliente=cliente,
        weeks=weeks,
        current_year=year,
        current_month=month,
        month_name=MONTH_NAMES[month],
        prev_month_url=prev_month_url,
        next_month_url=next_month_url,
        token=token,
    )


@bp.get("/editorial-share/<token>/publication/<int:publication_id>")
def publication_detail(token, publication_id):
    link = EditorialShareLink.query.filter_by(token=str(token), is_active=True).first()
    if not link:
        return {"error": "Link non valido"}, 404

    pub = EditorialPublication.query.get_or_404(publication_id)
    if pub.cliente_id != link.cliente_id:
        return {"error": "Pubblicazione non trovata"}, 404

    return {
        "id": pub.id,
        "title": pub.title,
        "caption": pub.caption,
        "publication_date": pub.publication_date.isoformat() if pub.publication_date else None,
        "platforms": pub.get_platforms(),
        "images": pub.get_image_paths(),
    }
