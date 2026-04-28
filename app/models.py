from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


VALID_USER_ROLES = ("admin", "operatore", "readonly")
TASK_CATEGORIES = (
    "social_media",
    "grafica",
    "amministrazione",
    "fotografia",
    "web",
    "commerciale",
    "generale",
)
TASK_STATUSES = (
    "da_fare",
    "in_corso",
    "in_revisione",
    "completata",
    "annullata",
)
TASK_PRIORITIES = (
    "bassa",
    "media",
    "alta",
    "urgente",
)
CALENDAR_EVENT_TYPES = (
    "appuntamento",
    "scadenza",
    "impegno_cliente",
    "promemoria",
    "generale",
)
FINANCE_MOVEMENT_TYPES = ("entrata", "uscita")
FINANCE_MOVEMENT_STATUSES = ("prevista", "effettiva")
FINANCE_EXPENSE_TYPES = ("fissa", "variabile")
FINANCE_CATEGORIES = (
    "pagamento_cliente",
    "fornitore",
    "software",
    "advertising",
    "consulenza",
    "attrezzatura",
    "tasse",
    "stipendio",
    "commercialista",
    "banca",
    "costituzione_societa",
    "generale",
)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="readonly")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email}>"


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


class Task(db.Model):
    __tablename__ = "erp_tasks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    note = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(40), nullable=False, default="generale")
    status = db.Column(db.String(40), nullable=False, default="da_fare")
    priority = db.Column(db.String(40), nullable=False, default="media")
    due_date = db.Column(db.Date, nullable=True)
    lavoro_id = db.Column(db.Integer, db.ForeignKey("lavori.id"), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    lavoro = db.relationship("Lavoro", backref="erp_tasks")
    cliente = db.relationship("Cliente", backref="erp_tasks")
    assignee = db.relationship("User", backref="assigned_tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "note": self.note,
            "category": self.category,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "lavoro_id": self.lavoro_id,
            "lavoro": (
                {"id": self.lavoro.id, "descrizione": self.lavoro.descrizione}
                if self.lavoro
                else None
            ),
            "cliente_id": self.cliente_id,
            "cliente": (
                {"id": self.cliente.id, "name": self.cliente.name}
                if self.cliente
                else None
            ),
            "assignee_id": self.assignee_id,
            "assignee": (
                {"id": self.assignee.id, "name": self.assignee.name, "email": self.assignee.email}
                if self.assignee
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CalendarEvent(db.Model):
    __tablename__ = "erp_calendar_events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_type = db.Column(db.String(40), nullable=False, default="generale")
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=True)
    lavoro_id = db.Column(db.Integer, db.ForeignKey("lavori.id"), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey("erp_tasks.id"), nullable=True)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    cliente = db.relationship("Cliente", backref="calendar_events")
    lavoro = db.relationship("Lavoro", backref="calendar_events")
    task = db.relationship("Task", backref="calendar_events")
    assigned_user = db.relationship("User", backref="calendar_events")

    def to_dict(self):
        return {
            "source": "calendar_event",
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "start_datetime": (
                self.start_datetime.isoformat() if self.start_datetime else None
            ),
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "cliente_id": self.cliente_id,
            "cliente": (
                {"id": self.cliente.id, "name": self.cliente.name}
                if self.cliente
                else None
            ),
            "lavoro_id": self.lavoro_id,
            "lavoro": (
                {"id": self.lavoro.id, "descrizione": self.lavoro.descrizione}
                if self.lavoro
                else None
            ),
            "task_id": self.task_id,
            "task": self.task.to_dict() if self.task else None,
            "assigned_user_id": self.assigned_user_id,
            "assigned_user": (
                {
                    "id": self.assigned_user.id,
                    "name": self.assigned_user.name,
                    "email": self.assigned_user.email,
                }
                if self.assigned_user
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FinancialMovement(db.Model):
    __tablename__ = "erp_financial_movements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    movement_type = db.Column(db.String(20), nullable=False)
    movement_status = db.Column(db.String(20), nullable=False, default="prevista")
    expense_type = db.Column(db.String(20), nullable=True)
    category = db.Column(db.String(50), nullable=False, default="generale")
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    movement_date = db.Column(db.Date, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=True)
    lavoro_id = db.Column(db.Integer, db.ForeignKey("lavori.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    cliente = db.relationship("Cliente", backref="financial_movements")
    lavoro = db.relationship("Lavoro", backref="financial_movements")
    creator = db.relationship("User", backref="financial_movements")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "movement_type": self.movement_type,
            "movement_status": self.movement_status,
            "expense_type": self.expense_type,
            "category": self.category,
            "amount": float(self.amount) if self.amount is not None else 0.0,
            "movement_date": (
                self.movement_date.isoformat() if self.movement_date else None
            ),
            "month": self.month,
            "year": self.year,
            "cliente_id": self.cliente_id,
            "cliente": (
                {"id": self.cliente.id, "name": self.cliente.name}
                if self.cliente
                else None
            ),
            "lavoro_id": self.lavoro_id,
            "lavoro": (
                {"id": self.lavoro.id, "descrizione": self.lavoro.descrizione}
                if self.lavoro
                else None
            ),
            "created_by": self.created_by,
            "creator": (
                {"id": self.creator.id, "name": self.creator.name, "email": self.creator.email}
                if self.creator
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


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
