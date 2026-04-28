from flask import Blueprint, jsonify, render_template, request

from ..extensions import db
from ..models import Cliente, Lavoro


bp = Blueprint("clienti", __name__)


@bp.route("/clienti/new", methods=["GET", "POST"])
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

    if request.method == "GET":
        return render_template("cliente_new.html")


@bp.route("/clienti")
def clienti():
    clienti_list = Cliente.query.all()
    return render_template("clienti.html", clienti=clienti_list)


@bp.route("/clienti/<int:cliente_id>")
def cliente_page(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template("cliente.html", cliente=cliente)


@bp.delete("/clienti/<int:cliente_id>")
def cliente_delete(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({"message": "Cliente eliminato con successo"})


@bp.route("/clienti/edit/<int:cliente_id>", methods=["GET", "PUT"])
def cliente_edit(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == "GET":
        return render_template("cliente_edit.html", cliente=cliente)
    if request.method == "PUT":
        dataFromJS = request.get_json()
        if not dataFromJS:
            return "Errore", 404
        print(dataFromJS)
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
            return {"Errore nell'aggiornamento dei dati!": str(e)}, 500
