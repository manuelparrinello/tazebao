import os
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Definiamo uno schema per i nomi dei vincoli
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Forza Flask a ricaricare i template ogni volta che cambiano
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Opzionale: disabilita la cache del browser per i file statici durante lo sviluppo
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
db = SQLAlchemy(app, metadata=metadata)
CORS(app)
migrate = Migrate(app, db, render_as_batch=True)

status_lavori = ["Completato", "In corso", "In attesa", "Da iniziare"]


@app.template_filter()
def euroFormat(value):
    value = float(value)
    return "{:.2f}".format(value).replace(".", ",")


@app.template_filter("nl2br")
def nl2br_filter(text):
    if text:
        return text.replace("\n", "<br>\n")
    return ""


######################## DB TABLES CREATION ########################


# DB MODEL - DEFINE CLIENTE
class Cliente(db.Model):
    __tablename__ = "clienti"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ragsoc = db.Column(db.String(100), nullable=False)
    indirizzo = db.Column(db.String(100), nullable=True)
    citta = db.Column(db.String(50), nullable=True)
    cap = db.Column(db.String(5), nullable=True)
    provincia = db.Column(db.String(2), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    p_iva = db.Column(db.String(30), nullable=True)
    sdi = db.Column(db.String(7), nullable=True)
    pec = db.Column(db.String(100), nullable=True)
    colore = db.Column(db.String(20), nullable=True)

    note = db.Column(db.Text, nullable=True)
    lavori = db.relationship(
        "Lavoro", backref="cliente", lazy=True, cascade="all, delete, delete-orphan"
    )
    preventivi = db.relationship(
        "Preventivo", backref="cliente", lazy=True, cascade="all, delete, delete-orphan"
    )

    def __repr__(self):
        return f"<Cliente {self.name}>"


# DB MODEL - DEFINE LAVORO
class Lavoro(db.Model):
    __tablename__ = "lavori"
    id = db.Column(db.Integer, primary_key=True)
    descrizione = db.Column(db.String(200), nullable=False)
    data_inizio = db.Column(db.Date, nullable=True)
    data_fine = db.Column(db.Date, nullable=True)
    data_pagamento = db.Column(db.Date, nullable=True)
    stato = db.Column(db.String(50), nullable=True)
    priorita = db.Column(db.String(50), nullable=True)
    preventivato = db.Column(db.Float, nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    tasks = db.relationship(
        "TaskLavoro", backref="lavoro", lazy=True, cascade="all, delete, delete-orphan"
    )
    preventivo_id = db.Column(db.Integer, db.ForeignKey("preventivi.id"), nullable=True)
    note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Lavoro {self.descrizione}>"


# DB MODEL - DEFINE TASKS LAVORO
class TaskLavoro(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    lavoro_id = db.Column(db.Integer, db.ForeignKey("lavori.id"), nullable=False)
    files = db.relationship(
        "TaskFile", backref="task", lazy=True, cascade="all, delete, delete-orphan"
    )
    note = db.Column(db.Text, nullable=False)


# DB MODEL - DEFINE TASK FILES
class TaskFile(db.Model):
    __tablename__ = "taskfile"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    size = db.Column(db.Float, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)


# DB MODEL - PREVENTIVI
class Preventivo(db.Model):
    __tablename__ = "preventivi"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    stato = db.Column(db.String(20), default="bozza", nullable=False)
    totale_preventivo = db.Column(db.Float, nullable=True)

    # 1 preventivo -> N lavori (se ti serve davvero questo legame)
    lavori = db.relationship(
        "Lavoro",
        backref="preventivo",  # su Lavoro avrai .preventivo
        lazy=True,
    )
    righe = db.relationship(
        "RigaPreventivo",
        back_populates="preventivo",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# DB MODEL - RIGHE PREVENTIVO
class RigaPreventivo(db.Model):
    __tablename__ = "righe_preventivo"
    id = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    descrizione = db.Column(db.Text, nullable=False)
    prezzo_ie = db.Column(db.Numeric(10, 2), nullable=False)
    prezzo_ii = db.Column(db.Numeric(10, 2), nullable=False)
    totale_riga = db.Column(db.Numeric(10, 2), nullable=False)
    preventivo = db.relationship("Preventivo", back_populates="righe")
    preventivo_id = db.Column(
        db.Integer, db.ForeignKey("preventivi.id"), nullable=False
    )


# CREATE DATABASE TABLES IF THEY DON'T EXIST ----------------
with app.app_context():
    db.create_all()


######################## ADD DB RECORDS ########################


# DB - NUOVO CLIENTE
@app.route("/clienti/new", methods=["GET", "POST"])
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


# DB - NUOVO LAVORO
@app.route("/lavori/new", methods=["GET", "POST"])
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

        # 1. Creiamo gli oggetti data PRIMA di usarli nel jsonify
        data_inizio_obj = convertToDate(data_inizio)
        data_fine_obj = convertToDate(data_fine)
        data_pagamento_obj = convertToDate(data_pagamento)

        if stato not in status_lavori:
            return

        # Aggiungi il nuovo lavoro al database
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


# DB - NUOVO PREVENTIVO
@app.route("/preventivi/nuovo", methods=["POST", "GET"])
def nuovo_preventivo():
    if request.method == "POST":
        iva = 1.22
        tasse_varie = 8.18
        data = request.get_json()
        cliente_id = data["cliente_id"]
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
        db.session.add(nuovo_preventivo)
        db.session.commit()

        return (
            jsonify(
                {
                    "cliente_id": cliente.id,
                    "preventivo_id": nuovo_preventivo.id,
                    "righe": [riga for riga in righe],
                }
            ),
            200,
        )
    return render_template("preventivo_new.html")


######################## ROUTES ########################


# HOMEPAGE
@app.route("/")
def index():
    return render_template(
        "index.html", title="Home", description="Welcome to the Home Page", path=db_path
    )


# LAVORI
@app.route("/lavori")
def lavori():
    lavori_list = Lavoro.query.all()
    return render_template("lavori.html", lavori=lavori_list)


# LAVORO SINGLE PAGE
@app.get("/lavori/<int:lavoro_id>")
def lavoro_page(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    return render_template("lavoro.html", lavoro=lavoro)


# CLIENTI
@app.route("/clienti")
def clienti():
    clienti_list = Cliente.query.all()
    return render_template("clienti.html", clienti=clienti_list)


# CLIENTE SINGLE PAGE
@app.route("/clienti/<int:cliente_id>")
def cliente_page(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template("cliente.html", cliente=cliente)


# RENDERIZZA Righe Preventivo
@app.get("/presentivi/addrow")
def render_row():
    id_riga = request.form.get("idRiga")
    qty = request.form.get("qty")
    descrizione = request.form.get("descrizione")
    prezzo = float(request.form.get("prezzo"))
    return jsonify(
        {"id_riga": id_riga, "qty": qty, "descrizione": descrizione, "prezzo": prezzo}
    )


@app.get("/preventivi/visualizza/<int:id>")
def visualizza_preventivo(id):
    preventivo = Preventivo.query.filter_by(id=id).first_or_404()
    return render_template("_preventivo.html", preventivo=preventivo)


######################## AZIONI ########################


# CLIENTE DELETE
@app.delete("/clienti/<int:cliente_id>")
def cliente_delete(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({"message": "Cliente eliminato con successo"})


# LAVORO DELETE
@app.delete("/lavori/<int:lavoro_id>")
def lavoro_delete(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    db.session.delete(lavoro)
    db.session.commit()
    return jsonify({"message": f"Lavoro '{lavoro.descrizione}' eliminato con successo"})


# LAVORO STATUS UPDATE
@app.patch("/lavori/<int:lavoro_id>")
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


# CLIENTE EDIT PAGE
@app.route("/clienti/edit/<int:cliente_id>", methods=["GET", "PUT"])
def cliente_edit(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == "GET":
        return render_template("cliente_edit.html", cliente=cliente)
    if request.method == "PUT":
        dataFromJS = request.get_json()
        if not dataFromJS:
            return "Errore", 404
        print(dataFromJS)
        # Aggiorna i campi del modello
        # Usiamo .get() per evitare errori se un campo manca nel JSON
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


######################## APIs ########################


# API - CLIENTI ALL
@app.get("/api/clienti/getall")
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


# API - LAVORI ALL
@app.get("/api/lavori/getall")
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


# API - LAVORO per ID
@app.get("/api/lavori/get/<int:id>")
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


# API - CLIENTE per ID
@app.get("/api/clienti/get/<int:cliente_id>")
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


# API - Recupero ID tramite Nome Cliente
@app.get("/api/clienti/getid/<string:nome>")
def get_ID_by_name(nome):
    cliente = Cliente.query.filter_by(name=nome).first()
    id = cliente.id
    print(id)
    return jsonify({"id": id})


######################## TESTING ########################
@app.route("/test")
def test():
    return render_template("base.html")


######################### MAIN ##########################
if __name__ == "__main__":
    app.run(debug=True)
