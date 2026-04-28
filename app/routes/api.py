from flask import Blueprint, jsonify

from ..models import Cliente, Lavoro, Preventivo


bp = Blueprint("api", __name__)


@bp.get("/api/clienti/getall")
def get_clienti():
    clienti = Cliente.query.all()
    return jsonify(
        [
            {
                "id": c.id,
                "nome": c.name,
                "telefono": c.telefono,
                "email": c.email,
                "note": c.note,
                "colore": c.colore,
                "count_lavori": Lavoro.query.filter_by(cliente_id=c.id).count(),
            }
            for c in clienti
        ]
    )


@bp.get("/api/lavori/getall")
def get_lavori():
    lavori = Lavoro.query.all()
    return jsonify(
        [
            {
                "id": l.id,
                "descrizione": l.descrizione,
                "data_inizio": l.data_inizio,
                "data_fine": l.data_fine,
                "data_pagamento": l.data_pagamento,
                "stato": l.stato,
                "priorita": l.priorita,
                "preventivato": l.preventivato,
                "cliente": {
                    "id": l.cliente.id,
                    "colore": l.cliente.colore,
                    "name": l.cliente.name,
                },
                "note": l.note,
            }
            for l in lavori
        ]
    )


@bp.get("/api/lavori/get/<int:id>")
def get_lavoro_byID(id):
    lavoro = Lavoro.query.get_or_404(id)
    return jsonify(
        {
            "id": lavoro.id,
            "descrizione": lavoro.descrizione,
            "data_inizio": lavoro.data_inizio,
            "data_fine": lavoro.data_fine,
            "data_pagamento": lavoro.data_pagamento,
            "priorita": lavoro.priorita,
            "stato": lavoro.stato,
            "preventivato": lavoro.preventivato,
            "note": lavoro.note,
            "cliente": {
                "nome": lavoro.cliente.name,
                "id": lavoro.cliente.id,
                "colore": lavoro.cliente.colore,
            },
        }
    )


@bp.get("/api/clienti/get/<int:cliente_id>")
def get_cliente_byID(cliente_id):
    c = Cliente.query.get_or_404(cliente_id)
    lavori = Lavoro.query.filter_by(cliente_id=cliente_id)
    countLavori = lavori.count()

    return jsonify(
        {
            "id": c.id,
            "nome": c.name,
            "ragsoc": c.ragsoc,
            "indirizzo": c.indirizzo,
            "citta": c.citta,
            "cap": c.cap,
            "provincia": c.provincia,
            "email": c.email,
            "telefono": c.telefono,
            "p_iva": c.p_iva,
            "sdi": c.sdi,
            "pec": c.pec,
            "colore": c.colore,
            "note": c.note,
            "count_lavori": countLavori,
            "lavori": [
                {
                    "id": lavoro.id,
                    "descrizione": lavoro.descrizione,
                    "stato": lavoro.stato,
                    "preventivato": lavoro.preventivato,
                    "data_inizio": lavoro.data_inizio,
                    "data_fine": lavoro.data_fine,
                    "data_pagamento": lavoro.data_pagamento,
                    "priorita": lavoro.priorita,
                    "note": lavoro.note,
                }
                for lavoro in lavori
            ],
        }
    )


@bp.get("/api/clienti/getid/<string:nome>")
def get_ID_by_name(nome):
    cliente = Cliente.query.filter_by(name=nome).first()
    id = cliente.id
    print(id)
    return jsonify({"id": id})


@bp.get("/api/preventivi/getall")
def get_preventivi():
    preventivi = Preventivo.query.all()
    return jsonify(
        [
            {
                "id": p.id,
                "descrizione": p.descrizione,
                "data": p.data_creazione,
                "cliente": Cliente.query.filter_by(id=p.cliente_id).first_or_404().name,
                "stato": p.stato,
                "totale_preventivo": p.totale_preventivo,
                "data_creazione": p.data_creazione.isoformat(),
                "lavoro": p.lavoro,
                "righe": [
                    {
                        "id": riga.id,
                        "qty": riga.qty,
                        "descrizione": riga.descrizione,
                        "prezzo_ie": riga.prezzo_ie,
                        "prezzo_ii": riga.prezzo_ii,
                        "totale_riga": riga.totale_riga,
                    }
                    for riga in p.righe
                ],
            }
            for p in preventivi
        ]
    )


@bp.get("/api/preventivi/get/<int:id>")
def get_preventivo_byID(id):
    preventivo = Preventivo.query.filter_by(id=id).first_or_404()
    return jsonify(
        {
            "id": preventivo.id,
            "cliente": preventivo.cliente,
            "data": preventivo.data_creazione,
            "stato": preventivo.stato,
            "lavoro": preventivo.lavoro,
            "totale_preventivo": float(preventivo.totale_preventivo),
            "cliente": {
                "nome": preventivo.cliente.name,
                "ragsoc": preventivo.cliente.ragsoc,
                "indirizzo": preventivo.cliente.indirizzo,
                "citta": preventivo.cliente.citta,
                "cap": preventivo.cliente.cap,
                "provincia": preventivo.cliente.provincia,
                "email": preventivo.cliente.email,
                "telefono": preventivo.cliente.telefono,
                "p_iva": preventivo.cliente.p_iva,
                "sdi": preventivo.cliente.sdi,
                "pec": preventivo.cliente.pec,
                "colore": preventivo.cliente.colore,
            },
            "righe": [
                {
                    "id": riga.id,
                    "qty": riga.qty,
                    "descrizione": riga.descrizione,
                    "prezzo_ie": float(riga.prezzo_ie),
                    "prezzo_ii": float(riga.prezzo_ii),
                    "totale_riga": float(riga.totale_riga),
                }
                for riga in preventivo.righe
            ],
        }
    )
