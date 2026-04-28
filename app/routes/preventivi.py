from decimal import Decimal

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from ..auth import login_required
from ..extensions import db
from ..models import Cliente, Preventivo, RigaPreventivo


bp = Blueprint("preventivi", __name__)

IVA = Decimal("1.22")
TASSE_VARIE = Decimal("8.18")
PREVENTIVO_STATUSES = ("bozza", "inviato", "accettato", "rifiutato")


def decimal_from_form(value, default="0"):
    normalized = (value or default).replace(",", ".")
    return Decimal(normalized)


def recalculate_preventivo(preventivo, righe_data):
    righe = []
    totale_preventivo = Decimal("0")

    for riga_data in righe_data:
        qty = decimal_from_form(riga_data.get("qty"), "1")
        prezzo_ie = decimal_from_form(riga_data.get("prezzo_ie"), "0")
        descrizione = (riga_data.get("descrizione") or "").strip()

        if qty <= 0 or not descrizione:
            continue

        prezzo_ii = prezzo_ie * IVA
        totale_riga = prezzo_ii * qty
        totale_preventivo += totale_riga
        righe.append(
            RigaPreventivo(
                qty=qty,
                descrizione=descrizione,
                prezzo_ie=prezzo_ie,
                prezzo_ii=prezzo_ii,
                totale_riga=totale_riga,
            )
        )

    preventivo.righe = righe
    preventivo.totale_preventivo = float(totale_preventivo + TASSE_VARIE)


@bp.route("/preventivi/nuovo", methods=["POST", "GET"])
@login_required
def nuovo_preventivo():
    if request.method == "POST":
        iva = 1.22
        tasse_varie = 8.18
        data = request.get_json()
        cliente_id = data["cliente_id"]
        descrizione = data["titolo_preventivo"]
        cliente = Cliente.query.filter_by(id=cliente_id).first()
        print("Cliente: " + cliente.name + ", ID: " + str(cliente.id))
        righe = [
            {
                "qty": riga["qty"],
                "descrizione": riga["descrizione"],
                "prezzo_ie": float(riga["prezzo"]),
                "prezzo_ii": float(riga["prezzo"]) * iva,
                "totale": (float(riga["prezzo"]) * iva) * float(riga["qty"]),
            }
            for riga in data["righe"]
        ]
        nuovo_preventivo = Preventivo(
            descrizione=descrizione,
            cliente_id=cliente_id,
            righe=[
                RigaPreventivo(
                    qty=riga["qty"],
                    descrizione=riga["descrizione"],
                    prezzo_ie=float(riga["prezzo_ie"]),
                    prezzo_ii=float(riga["prezzo_ie"]) * iva,
                    totale_riga=float(riga["prezzo_ii"]) * float(riga["qty"]),
                )
                for riga in righe
            ],
            totale_preventivo=sum((riga["totale"]) for riga in righe) + tasse_varie,
        )
        subtotale = 0

        for riga in data["righe"]:
            subtotale += riga["totaleRiga"]
            print(f"TOTALE RIGA: {riga['totaleRiga']}")
            print(f"SUBTOTALE: {subtotale}")

        db.session.add(nuovo_preventivo)
        db.session.commit()

        return (
            jsonify(
                {
                    "cliente_id": cliente.id,
                    "cliente_nome": cliente.name,
                    "ragsoc": cliente.ragsoc,
                    "indirizzo": cliente.indirizzo,
                    "citta": cliente.citta,
                    "cap": cliente.cap,
                    "provincia": cliente.provincia,
                    "email": cliente.email,
                    "telefono": cliente.telefono,
                    "p_iva": cliente.p_iva,
                    "sdi": cliente.sdi,
                    "pec": cliente.pec,
                    "preventivo_id": nuovo_preventivo.id,
                    "righe": [riga for riga in righe],
                    "subtotale": subtotale,
                }
            ),
            200,
        )
    return render_template("preventivo_new.html")


@bp.get("/preventivi")
@login_required
def preventivi():
    return render_template("preventivi.html")


@bp.get("/presentivi/addrow")
@bp.get("/preventivi/addrow")
def render_row():
    id_riga = request.form.get("idRiga")
    qty = request.form.get("qty")
    descrizione = request.form.get("descrizione")
    prezzo = float(request.form.get("prezzo"))
    return jsonify(
        {"id_riga": id_riga, "qty": qty, "descrizione": descrizione, "prezzo": prezzo}
    )


@bp.get("/preventivi/visualizza/<int:id>")
@login_required
def visualizza_preventivo(id):
    preventivo = Preventivo.query.filter_by(id=id).first_or_404()
    return render_template("_preventivo.html", preventivo=preventivo)


@bp.route("/preventivi/<int:id>/edit", methods=["GET", "POST"])
@login_required
def preventivo_edit(id):
    preventivo = Preventivo.query.filter_by(id=id).first_or_404()
    clienti = Cliente.query.order_by(Cliente.name.asc()).all()
    status_values = sorted(
        {
            *PREVENTIVO_STATUSES,
            *[
                stato
                for (stato,) in db.session.query(Preventivo.stato).distinct().all()
                if stato
            ],
        }
    )

    if request.method == "POST":
        preventivo.cliente_id = int(request.form.get("cliente_id"))
        preventivo.stato = request.form.get("stato") or "bozza"
        preventivo.descrizione = (
            request.form.get("descrizione") or preventivo.descrizione or ""
        ).strip()

        righe_data = []
        qty_values = request.form.getlist("qty[]")
        descrizioni = request.form.getlist("riga_descrizione[]")
        prezzi = request.form.getlist("prezzo_ie[]")

        for index, qty in enumerate(qty_values):
            righe_data.append(
                {
                    "qty": qty,
                    "descrizione": descrizioni[index] if index < len(descrizioni) else "",
                    "prezzo_ie": prezzi[index] if index < len(prezzi) else "0",
                }
            )

        recalculate_preventivo(preventivo, righe_data)
        db.session.commit()
        return redirect(url_for("preventivi.visualizza_preventivo", id=preventivo.id))

    return render_template(
        "preventivo_edit.html",
        preventivo=preventivo,
        clienti=clienti,
        status_values=status_values,
        iva=IVA,
        tasse_varie=TASSE_VARIE,
    )
