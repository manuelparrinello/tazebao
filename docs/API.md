# API REST

Tutti gli endpoint sotto `/api/` registrati sul blueprint `api.bp`. **CSRF esente** per tutto il blueprint. Autenticazione via cookie di sessione Flask.

Formato risposta standard: `{"success": bool, "data": any, "error": string|null}`

## Dashboard

### `GET /api/dashboard/summary`
**Guard**: `login_required`

Riepilogo dashboard: conteggi, notifiche, movimenti recenti, finance summary.

**Response** `200`:
```json
{
  "success": true,
  "data": {
    "notifications": [],
    "open_task_count": 0,
    "task_due_soon_count": 0,
    "overdue_task_count": 0,
    "upcoming_events_count": 0,
    "active_clients_count": 0,
    "active_jobs_count": 0,
    "pending_quotes_count": 0,
    "draft_quotes_count": 0,
    "accepted_quotes_count": 0,
    "upcoming_publications_count": 0,
    "expected_income_count": 0,
    "expected_income_sum": 0.0,
    "recent_tasks": [],
    "upcoming_events": [],
    "upcoming_publications": [],
    "recent_quotes": [],
    "today_items": [],
    "recent_updates": [],
    "unread_mail_count": 0,
    "current_balance": 0.0,
    "month_income_effective": 0.0,
    "month_income_expected": 0.0,
    "month_expenses_fixed": 0.0,
    "month_expenses_variable": 0.0,
    "month_expenses_total": 0.0,
    "month_balance": 0.0
  }
}
```

### `GET /api/search`
**Guard**: `login_required`

Ricerca globale JSON (stessa logica di `/search` HTML).

**Query**: `?q=test`

**Response** `200`:
```json
{
  "results": [
    {"type": "cliente", "id": 1, "label": "...", "subtitle": "...", "icon": "bi-people", "url": "/clienti/1"}
  ]
}
```

## Finance

### `GET /api/finance`
**Guard**: `login_required`

Elenco tutti i movimenti finanziari.

**Response** `200`: `{"success": true, "data": [movement.to_dict(), ...]}`

### `GET /api/finance/<int:movement_id>`
**Guard**: `login_required`

Dettaglio movimento.

**Response** `200` / `404`

### `POST /api/finance`
**Guard**: `role_required("admin", "operatore")`

Crea movimento finanziario.

**Body**:
```json
{
  "title": "Fattura XYZ",
  "movement_type": "entrata",
  "movement_status": "prevista",
  "category": "pagamento_cliente",
  "amount": 1500.00,
  "movement_date": "2024-01-15",
  "cliente_id": 1,
  "lavoro_id": null
}
```

**Response** `201` / `400`

### `PATCH /api/finance/<int:movement_id>`
**Guard**: `role_required("admin", "operatore")`

Aggiornamento parziale movimento.

**Body** (parziale): `{"amount": 2000.00}`

**Response** `200` / `400` / `404`

### `DELETE /api/finance/<int:movement_id>`
**Guard**: `role_required("admin", "operatore")`

Elimina movimento.

**Response** `200` (dati movimento eliminato) / `404`

### `GET /api/finance/summary`
**Guard**: `login_required`

Riepilogo finanziario mensile.

**Query**: `?year=2024&month=1`

**Response** `200` / `400`

## Email Logs (comunicazioni)

### `GET /api/emails`
**Guard**: `login_required`

Elenco log comunicazioni. Filtro: `?cliente_id=1`

**Response** `200`

### `GET /api/emails/<int:email_id>`
**Guard**: `login_required`

Dettaglio comunicazione.

**Response** `200` / `404`

### `POST /api/emails`
**Guard**: `role_required("admin", "operatore")`

Crea comunicazione.

**Body**:
```json
{
  "subject": "Richiesta preventivo",
  "body": "Testo...",
  "direction": "outbound",
  "email_address": "cliente@example.com",
  "cliente_id": 1,
  "sent_at": "2024-01-15T10:00:00"
}
```

**Response** `201` / `400`

### `PATCH /api/emails/<int:email_id>`
**Guard**: `role_required("admin", "operatore")`

Aggiornamento parziale.

**Response** `200` / `400` / `404`

### `DELETE /api/emails/<int:email_id>`
**Guard**: `role_required("admin", "operatore")`

Elimina comunicazione.

**Response** `200` / `404`

## Tasks

### `GET /api/tasks`
**Guard**: `login_required`

Elenco tutte le task.

**Response** `200`

### `GET /api/tasks/<int:task_id>`
**Guard**: `login_required`

Dettaglio task.

**Response** `200` / `404`

### `POST /api/tasks`
**Guard**: `role_required("admin", "operatore")`

Crea task.

**Body**:
```json
{
  "name": "Nuovo task",
  "category": "grafica",
  "status": "da_fare",
  "priority": "media",
  "due_date": "2024-02-01",
  "cliente_id": 1,
  "lavoro_id": null,
  "assignee_id": 1
}
```

**Response** `201` / `400`

### `PATCH /api/tasks/<int:task_id>`
**Guard**: `role_required("admin", "operatore")`

Aggiornamento parziale task.

**Response** `200` / `400` / `404`

### `DELETE /api/tasks/<int:task_id>`
**Guard**: `role_required("admin", "operatore")`

Annulla task (imposta status="annullata", non elimina fisicamente).

**Response** `200` / `404`

## Calendar Events

### `GET /api/calendar/events`
**Guard**: `login_required`

Elenco eventi calendario + scadenze task (merged, sorted).

**Response** `200`

### `GET /api/calendar/events/<int:event_id>`
**Guard**: `login_required`

Dettaglio evento.

**Response** `200` / `404`

### `POST /api/calendar/events`
**Guard**: `role_required("admin", "operatore")`

Crea evento.

**Body**:
```json
{
  "title": "Riunione",
  "event_type": "appuntamento",
  "start_datetime": "2024-01-15T14:00:00",
  "end_datetime": "2024-01-15T15:00:00",
  "cliente_id": 1,
  "assigned_user_id": 1
}
```

**Response** `201` / `400`

### `PATCH /api/calendar/events/<int:event_id>`
**Guard**: `role_required("admin", "operatore")`

Aggiornamento parziale evento.

**Response** `200` / `400` / `404`

### `DELETE /api/calendar/events/<int:event_id>`
**Guard**: `role_required("admin", "operatore")`

Elimina evento.

**Response** `200` / `404`

## Dati anagrafici (legacy API)

Questi endpoint restituiscono JSON non standard (senza wrapper `success/data/error`).

### `GET /api/clienti/getall`
**Guard**: `login_required`

Elenco clienti con conteggio lavori.

**Response** `200`:
```json
[
  {"id": 1, "nome": "...", "telefono": "...", "email": "...", "note": "...", "colore": "...", "count_lavori": 0}
]
```

### `GET /api/clienti/get/<int:cliente_id>`
**Guard**: `login_required`

Dettaglio cliente con lista lavori.

**Response** `200` / `404`

### `GET /api/clienti/getid/<string:nome>`
**Guard**: `login_required`

Ottiene ID cliente per nome esatto.

**Response** `200`: `{"id": 1}`

### `GET /api/lavori/getall`
**Guard**: `login_required`

Elenco lavori con dati cliente.

**Response** `200`

### `GET /api/lavori/get/<int:id>`
**Guard**: `login_required`

Dettaglio lavoro.

**Response** `200` / `404`

### `GET /api/preventivi/getall`
**Guard**: `login_required`

Elenco preventivi ERP + preventivi PDF esterni (da Lavoro con preventivo_pdf_path).

**Response** `200`

### `GET /api/preventivi/get/<int:id>`
**Guard**: `login_required`

Dettaglio preventivo con righe e dati cliente.

**Response** `200` / `404`

## Riepilogo endpoint API

| Metodo | URL | Auth | CSRF |
|--------|-----|------|------|
| GET | `/api/search` | login | esente |
| GET | `/api/dashboard/summary` | login | esente |
| GET | `/api/finance` | login | esente |
| GET | `/api/finance/<id>` | login | esente |
| POST | `/api/finance` | admin, operatore | esente |
| PATCH | `/api/finance/<id>` | admin, operatore | esente |
| DELETE | `/api/finance/<id>` | admin, operatore | esente |
| GET | `/api/finance/summary` | login | esente |
| GET | `/api/emails` | login | esente |
| GET | `/api/emails/<id>` | login | esente |
| POST | `/api/emails` | admin, operatore | esente |
| PATCH | `/api/emails/<id>` | admin, operatore | esente |
| DELETE | `/api/emails/<id>` | admin, operatore | esente |
| GET | `/api/tasks` | login | esente |
| GET | `/api/tasks/<id>` | login | esente |
| POST | `/api/tasks` | admin, operatore | esente |
| PATCH | `/api/tasks/<id>` | admin, operatore | esente |
| DELETE | `/api/tasks/<id>` | admin, operatore | esente |
| GET | `/api/calendar/events` | login | esente |
| GET | `/api/calendar/events/<id>` | login | esente |
| POST | `/api/calendar/events` | admin, operatore | esente |
| PATCH | `/api/calendar/events/<id>` | admin, operatore | esente |
| DELETE | `/api/calendar/events/<id>` | admin, operatore | esente |
| GET | `/api/clienti/getall` | login | esente |
| GET | `/api/clienti/get/<id>` | login | esente |
| GET | `/api/clienti/getid/<nome>` | login | esente |
| GET | `/api/lavori/getall` | login | esente |
| GET | `/api/lavori/get/<id>` | login | esente |
| GET | `/api/preventivi/getall` | login | esente |
| GET | `/api/preventivi/get/<id>` | login | esente |

**Nota**: gli endpoint `/api/clienti/*`, `/api/lavori/*`, `/api/preventivi/*` sono anche registrati come alias legacy endpoint con URL brevi (es. `/api/clienti/getall`) tramite `register_legacy_endpoint_aliases` in `__init__.py`.
