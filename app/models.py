from datetime import datetime

from .extensions import db


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


class Lavoro(db.Model):
    __tablename__ = "lavori"
    id = db.Column(db.Integer, primary_key=True)
    descrizione = db.Column(db.String(200), nullable=False)
    data_inizio = db.Column(db.Date, nullable=True)
    data_fine = db.Column(db.Date, nullable=True)
    data_pagamento = db.Column(db.Date, nullable=True)
    stato = db.Column(db.String(50), nullable=True)
    priorita = db.Column(db.String(50), nullable=True)
    preventivi = db.relationship(
        "Preventivo",
        backref="lavoro",
        lazy=True,
        cascade="all, delete, delete-orphan",
    )
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    tasks = db.relationship(
        "TaskLavoro", backref="lavoro", lazy=True, cascade="all, delete, delete-orphan"
    )

    def __repr__(self):
        return f"<Lavoro {self.descrizione}>"


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


class TaskFile(db.Model):
    __tablename__ = "taskfile"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    size = db.Column(db.Float, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)


class Preventivo(db.Model):
    __tablename__ = "preventivi"
    id = db.Column(db.Integer, primary_key=True)
    descrizione = db.Column(db.String(200), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    stato = db.Column(db.String(20), default="bozza", nullable=False)
    totale_preventivo = db.Column(db.Float, nullable=True)
    lavoro_id = db.Column(db.Integer, db.ForeignKey("lavori.id"), nullable=True)
    righe = db.relationship(
        "RigaPreventivo",
        back_populates="preventivo",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


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
