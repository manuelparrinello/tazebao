from flask import Blueprint, jsonify, render_template, request

from ..extensions import db
from ..models import Cliente, Preventivo, RigaPreventivo


bp = Blueprint("preventivi", __name__)


@bp.route("/preventivi/nuovo", methods=["POST", "GET"])
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
def visualizza_preventivo(id):
    preventivo = Preventivo.query.filter_by(id=id).first_or_404()
    return render_template("_preventivo.html", preventivo=preventivo)
