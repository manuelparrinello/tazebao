from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_cors import CORS
from flask_migrate import Migrate
import os
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


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

######################## DB TABLES CREATION ########################


# DB - DEFINE CLIENTE
class Cliente(db.Model):
    __tablename__ = "clienti"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
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

    def __repr__(self):
        return f"<Cliente {self.name}>"


# DB - DEFINE LAVORO
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
    note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Lavoro {self.descrizione}>"


# DB - DEFINE TASKS LAVORO
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


# DB - DEFINE TASK FILES


class TaskFile(db.Model):
    __tablename__ = "taskfile"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    size = db.Column(db.Float, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)


# CREATE DATABASE TABLES IF THEY DON'T EXIST ----------------
with app.app_context():
    db.create_all()


######################## ADD DB RECORDS ########################


# DB - NUOVO CLIENTE
@app.route("/clienti/new", methods=["GET", "POST"])
def nuovo_cliente():
    if request.method == "POST":
        nomeCliente = request.form.get("nome_cliente").title()
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
        # Aggiungi il nuovo cliente al database
        nuovo_cliente = Cliente(
            name=nomeCliente,
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
                        "nome": nomeCliente,
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


# NUOVO PREVENTIVO
@app.route("/preventivi/nuovo", methods=["POST", "GET"])
def nuovo_preventivo():
    if request.method == "POST":
        iva = 1.22
        cliente_id = request.form.get("cliente")
        cliente_q = Cliente.query.filter_by(id=cliente_id).first()
        cliente = cliente_q.name
        indirizzo = cliente_q.indirizzo
        cap = cliente_q.cap
        citta = cliente_q.citta
        provincia = cliente_q.provincia
        email = cliente_q.email
        telefono = cliente_q.telefono
        p_iva = cliente_q.p_iva
        sdi = cliente_q.sdi
        pec = cliente_q.pec
        prezzo = request.form.get("prezzo")
        prezzo_ii = float(prezzo) * iva
        qty = float(request.form.get("qty"))
        qty= int(qty)
        prezzo_subtotale = prezzo_ii * qty
        tasse_varie = 8
        totale = tasse_varie + prezzo_subtotale
        descrizione = request.form.get("descrizione")

        # QUESTO E' L'URL CHE SI VEDRA' SUL DOCUMENTO PREVENTIVO COMPILATO:
        target_url = url_for(
            "visualizza_preventivo",
            cliente=cliente,
            indirizzo=indirizzo,
            cap=cap,
            citta=citta,
            provincia=provincia,
            email=email,
            telefono=telefono,
            p_iva=p_iva,
            sdi=sdi,
            pec=pec,
            prezzo=prezzo,
            prezzo_ii=prezzo_ii,
            prezzo_subtotale=prezzo_subtotale,
            tasse_varie=tasse_varie,
            totale=totale,
            descrizione=descrizione,
            qty=qty
        )
        return jsonify({"target_url": target_url})
    return render_template("preventivo_new.html")


# ->
# -> QUI SI INSERISCE LA RICHIESTA GET (window.location.ref)
# CHE VIENE GESTITA DALLA ROUTE QUI IN BASSO


@app.get("/preventivi/visualizza")
def visualizza_preventivo():
    # Recupero il dato tramite il query params passato
    cliente = request.args.get("cliente", "Nessun cliente")
    indirizzo = request.args.get("indirizzo", "Nessun indirizzo")
    cap = request.args.get("cap", "Nessun cap")
    citta = request.args.get("citta", "Nessuna citta")
    provincia = request.args.get("provincia", "Nessuna provincia")
    email = request.args.get("email", "Nessuna email")
    telefono = request.args.get("telefono", "Nessun telefono")
    p_iva = request.args.get("p_iva", "Nessuna p_iva")
    sdi = request.args.get("sdi", "Nessuno sdi")
    pec = request.args.get("pec", "Nessuna pec")
    prezzo = request.args.get("prezzo", "Nessun cliente")
    prezzo_ii = request.args.get("prezzo_ii", "Nessun cliente")
    prezzo_subtotale = request.args.get("prezzo_subtotale", "Nessun cliente")
    tasse_varie = request.args.get("tasse_varie", "Nessun cliente")
    totale = request.args.get("totale", "Nessun dato")
    descrizione = request.args.get("descrizione", "Nessun dato")
    qty=request.args.get("qty", "Nessun dato")

    # print(f"IL DATO CHE FLASK STA PASSANDO: {titolo_prova}")

    # Qui l'URL è già generato.. Questa riga serve solo a inserire la variabile "dato" sulla pagina, passata tramite query params
    return render_template(
        "_preventivo.html",
        cliente=cliente,
        indirizzo=indirizzo,
        cap=cap,
        citta=citta,
        provincia=provincia,
        email=email,
        telefono=telefono,
        p_iva=p_iva,
        sdi=sdi,
        pec=pec,
        prezzo=prezzo,
        prezzo_ii=prezzo_ii,
        prezzo_subtotale=prezzo_subtotale,
        tasse_varie=tasse_varie,
        totale=totale,
        descrizione=descrizione,
        qty=qty
    )


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
