from flask import Flask, jsonify, render_template, request, flash
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)

# DEFINE DATABASE MODELS HERE IF NEEDED --------------------
class Cliente(db.Model): 
    __tablename__ = 'clienti'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    lavori = db.relationship('Lavoro', backref='cliente', lazy=True)
    note = db.Column(db.Text, nullable=True)
    colore = db.Column(db.String(20), nullable=True)
    
    def __repr__(self):
        return f"<Cliente {self.name}>"
    
class Lavoro(db.Model):
    __tablename__ = 'lavori'
    id = db.Column(db.Integer, primary_key=True)
    descrizione = db.Column(db.String(200), nullable=False)
    data_inizio = db.Column(db.Date, nullable=True)
    data_fine = db.Column(db.Date, nullable=True)
    data_pagamento = db.Column(db.Date, nullable=True)
    stato = db.Column(db.String(50), nullable=True)
    priorita = db.Column(db.String(50), nullable=True)
    preventivato = db.Column(db.Float, nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False)
    note = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"<Lavoro {self.descrizione}>"

# CREATE DATABASE TABLES IF THEY DON'T EXIST ----------------    
with app.app_context():
    db.create_all()
    
# DEFINE ROUTES HERE --------------------------------------
# Home route
@app.route('/')
def index():
    return(render_template('index.html', title='Home', description='Welcome to the Home Page', path=db_path))

# Nuovo cliente route
@app.route('/cliente/new', methods=['GET', 'POST'])
def nuovo_cliente():
    if request.method == 'POST':
        nomeCliente = request.form.get('nomeCliente').title()
        telefono = request.form.get('telefono')
        email = request.form.get('email').lower()
        note = request.form.get('note')
        colore = request.form.get('colore')
        # Aggiungi il nuovo cliente al database
        nuovo_cliente = Cliente(
            name=nomeCliente,
            telefono=telefono,
            email=email,
            note=note,
            colore=colore
        )
        db.session.add(nuovo_cliente)
        db.session.commit()
        return jsonify({'message': 'Cliente aggiunto con successo!'}), 201
    
    if request.method == 'GET':
        return render_template('cliente_new.html')

# Clienti route
@app.route('/clienti')
def clienti():
    clienti_list = Cliente.query.all()
    return render_template('clienti.html', clienti=clienti_list)

# Nuovo lavoro route
@app.route('/lavoro/new', methods=['GET', 'POST'])
def nuovo_lavoro():
    if request.method == 'POST':
        descrizione = request.form.get('descrizione')
        data_inizio = request.form.get('data_inizio')
        data_fine = request.form.get('data_fine')
        data_pagamento = request.form.get('data_pagamento')
        cliente_id = request.form.get('cliente_id')
        priorita = request.form.get('priorita')
        stato = request.form.get('stato')
        preventivato = request.form.get('preventivato')
        note = request.form.get('note')
        
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
            note=note
        )
        db.session.add(nuovo_lavoro)
        db.session.commit()
        return jsonify({'message': 'Lavoro aggiunto con successo!'}), 201
    
    if request.method == 'GET':
        clienti_list = Cliente.query.all()
        return render_template('lavoro_new.html', clienti=clienti_list)
    
# Lavori route
@app.route('/lavori')
def lavori():
    lavori_list = Lavoro.query.all()
    return render_template('lavori.html', lavori=lavori_list)

# Cliente page route
@app.route('/clienti/<int:cliente_id>')
def cliente_page(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template('cliente.html', cliente=cliente) 

# testing route
@app.route('/test')
def test():
    return render_template('base.html')


if __name__ == '__main__':
    app.run(debug=True)