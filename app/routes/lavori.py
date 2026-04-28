from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from ..extensions import db
from ..models import Cliente, Lavoro


bp = Blueprint("lavori", __name__)

status_lavori = ["Completato", "In corso", "In attesa", "Da iniziare"]


@bp.route("/lavori/new", methods=["GET", "POST"])
def nuovo_lavoro():
    if request.method == "POST":
        descrizione = request.form.get("descrizione")
        data_inizio = request.form.get("data_inizio")
        data_fine = request.form.get("data_fine")
        data_pagamento = request.form.get("data_pagamento")
        cliente_id = request.form.get("cliente_id")
        priorita = request.form.get("priorita")
        stato = request.form.get("stato")
        preventivato = request.form.get("preventivato")
        note = request.form.get("note")

        def convertToDate(data_string):
            if data_string:
                return datetime.strptime(data_string, "%Y-%m-%d").date()
            return None

        data_inizio_obj = convertToDate(data_inizio)
        data_fine_obj = convertToDate(data_fine)
        data_pagamento_obj = convertToDate(data_pagamento)

        if stato not in status_lavori:
            return

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

    if request.method == "GET":
        clienti_list = Cliente.query.all()
        return render_template("lavoro_new.html", clienti=clienti_list)


@bp.route("/lavori")
def lavori():
    lavori_list = Lavoro.query.all()
    return render_template("lavori.html", lavori=lavori_list)


@bp.get("/lavori/<int:lavoro_id>")
def lavoro_page(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    return render_template("lavoro.html", lavoro=lavoro)


@bp.delete("/lavori/<int:lavoro_id>")
def lavoro_delete(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    db.session.delete(lavoro)
    db.session.commit()
    return jsonify({"message": f"Lavoro '{lavoro.descrizione}' eliminato con successo"})


@bp.patch("/lavori/<int:lavoro_id>")
def status_lavoro_update(lavoro_id):
    lavoro = Lavoro.query.filter_by(id=lavoro_id).first()
    data = request.get_json()
    new_status = data["new_status"]
    if new_status not in status_lavori:
        db.session.rollback()
        return
    lavoro.stato = new_status
    db.session.commit()
    return jsonify(
        {
            "lavoro_id": lavoro.id,
            "lavoro_descrizione": lavoro.descrizione,
            "cliente": lavoro.cliente.name,
            "nuovo_stato": new_status,
        }
    )
