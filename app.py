from flask import Flask, jsonify, render_template
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
    ragione_sociale = db.Column(db.String(150), nullable=True)
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
    data_inizio = db.Column(db.Date, nullable=False)
    data_fine = db.Column(db.Date, nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False)
    
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
@app.route('/cliente/new')
def nuovo_cliente():
    return render_template('cliente_new.html')

# Clienti route
@app.route('/clienti')
def clienti():
    clienti_list = Cliente.query.all()
    return render_template('clienti.html', clienti=clienti_list)

# testing route
@app.route('/test')
def test():
    return render_template('base.html')


if __name__ == '__main__':
    app.run(debug=True)