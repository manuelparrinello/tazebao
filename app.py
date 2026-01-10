from flask import Flask, jsonify, render_template, request, redirect
from flask_cors import CORS
from babel.numbers import format_currency
import os
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
CORS(app)


def format_euro(value):
    try:
        return (
            f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
        )
    except (TypeError, ValueError):
        return "0,00 €"


app.jinja_env.filters["euro"] = format_euro


# DEFINE DATABASE MODELS HERE IF NEEDED --------------------
class Cliente(db.Model):
    __tablename__ = "clienti"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    lavori = db.relationship(
        "Lavoro", backref="cliente", lazy=True, cascade="all, delete, delete-orphan"
    )
    note = db.Column(db.Text, nullable=True)
    colore = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Cliente {self.name}>"


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
    note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Lavoro {self.descrizione}>"


# CREATE DATABASE TABLES IF THEY DON'T EXIST ----------------
with app.app_context():
    db.create_all()



######################## ADD DB RECORDS ########################

# DB - NUOVO CLIENTE
@app.route("/clienti/new", methods=["GET", "POST"])
def nuovo_cliente():
    if request.method == "POST":
        nomeCliente = request.form.get("nomeCliente").title()
        telefono = request.form.get("telefono")
        email = request.form.get("email").lower()
        note = request.form.get("note")
        colore = request.form.get("colore")
        # Aggiungi il nuovo cliente al database
        nuovo_cliente = Cliente(
            name=nomeCliente, telefono=telefono, email=email, note=note, colore=colore
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

        # Aggiungi il nuovo lavoro al database
        nuovo_lavoro = Lavoro(
            descrizione=descrizione,
            data_inizio=data_inizio,
            data_fine=data_fine,
            data_pagamento=data_pagamento,
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
                        "data_inizio": data_inizio,
                        "data_fine": data_fine,
                        "data_pagamento": data_pagamento,
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
        print(clienti_list)
        return render_template("lavoro_new.html", clienti=clienti_list)



######################## HTML PAGES ########################

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



######################## AZIONI ########################

# CLIENTE DELETE
@app.delete("/clienti/<int:cliente_id>")
def cliente_delete(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    return "", 204

# LAVORO DELETE 
@app.delete("/lavori/<int:lavoro_id>")
def lavoro_delete(lavoro_id):
    lavoro = Lavoro.query.get_or_404(lavoro_id)
    db.session.delete(lavoro)
    db.session.commit()
    return "", 204



######################## APIs ########################

# API - CLIENTI ALL
@app.get("/api/clienti/getall")
def get_clienti():
    fetched_clienti = Cliente.query.all()
    return jsonify(
        [
            {
                "id": c.id,
                "nome": c.name,
                "telefono": c.telefono,
                "email": c.email,
                "note": c.note,
                "colore": c.colore,
            }
            for c in fetched_clienti
        ]
    )

# API - LAVORI ALL
@app.get("/api/lavori/getall")
def get_lavori():
    lavori = Lavoro.query.all()
    return jsonify(
        [
            {
                "id" : l.id,
                "descrizione" : l.descrizione,
                "data_inizio" : l.data_inizio,
                "data_fine" : l.data_fine,
                "data_pagamento" : l.data_pagamento,
                "stato" : l.stato,
                "priorita" : l.priorita,
                "preventivato" : l.preventivato,
                "cliente" : {
                    "id" : l.cliente.id,
                    "colore" : l.cliente.colore,
                    "nome" : l.cliente.name
                },
                "note" : l.note
            }
            for l in lavori
        ]
    )

# API - CLIENTE per ID
@app.get("/api/clienti/get/<int:cliente_id>")
def get_cliente_byID(cliente_id):
    c = Cliente.query.get_or_404(cliente_id)
    countLavori = Lavoro.query.filter_by(cliente_id = cliente_id).count()
    return jsonify(
        {
            "id": c.id,
            "nome": c.name,
            "telefono": c.telefono,
            "email": c.email,
            "note": c.note,
            "colore": c.colore,
            "count_lavori" : countLavori
        }
    )



######################## TESTING ########################
@app.route("/test")
def test():
    return render_template("base.html")


######################### MAIN ##########################
if __name__ == "__main__":
    app.run(debug=True)
