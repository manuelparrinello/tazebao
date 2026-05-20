# API REST

Tutti gli endpoint sotto `/api/`. **CSRF esente** per tutto il blueprint `api.bp`.
Autenticazione via cookie di sessione Flask (nessun JWT / API key).

## Formato risposta standard

```
200 OK / 201 Created:
  {"success": true, "data": {...}, "error": null}

400 Bad Request:
  {"success": false, "data": null, "error": "messaggio"}

401 Unauthorized:
  {"success": false, "data": null, "error": "Authentication required"}

403 Forbidden:
  {"success": false, "data": null, "error": "Forbidden"}

404 Not Found:
  {"success": false, "data": null, "error": "Risorsa non trovata."}

500 Internal Server Error:
  {"success": false, "data": null, "error": "messaggio"}
```

## Dashboard

### `GET /api/dashboard/summary`
**Auth**: `login_required`

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

**Status**: 200, 500

### `GET /api/search`
**Auth**: `login_required`

Ricerca globale multi-entity (clienti, lavori, task, preventivi, finance, editoriali, calendario, moodboard).

**Query**: `?q=test`

**Response** `200`:
```json
{
  "success": true,
  "data": {
    "results": [
      {"type": "cliente", "id": 1, "label": "...", "subtitle": "...", "icon": "bi-people", "url": "/clienti/1"}
    ]
  }
}
```

**Status**: 200

## Finance

### `GET /api/finance`
**Auth**: `login_required`

Elenco tutti i movimenti finanziari.

**Response** `200`:
```json
{"success": true, "data": [movement.to_dict(), ...], "error": null}
```

**Status**: 200

### `GET /api/finance/<int:movement_id>`
**Auth**: `login_required`

Dettaglio movimento.

**Response** `200` / `404`

**Status**: 200, 404

### `POST /api/finance`
**Auth**: `role_required("admin", "operatore")`

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

**Status**: 201, 400

### `PATCH /api/finance/<int:movement_id>`
**Auth**: `role_required("admin", "operatore")`

Aggiornamento parziale movimento.

**Body** (parziale): `{"amount": 2000.00}`

**Status**: 200, 400, 404

### `DELETE /api/finance/<int:movement_id>`
**Auth**: `role_required("admin", "operatore")`

Elimina movimento.

**Response** `200` (dati movimento eliminato) / `404`

**Status**: 200, 404

### `GET /api/finance/summary`
**Auth**: `login_required`

Riepilogo finanziario mensile.

**Query**: `?year=2024&month=1`

**Status**: 200, 400

## Email Logs (comunicazioni)

### `GET /api/emails`
**Auth**: `login_required`

Elenco log comunicazioni.

**Query**: `?cliente_id=1`

**Status**: 200

### `GET /api/emails/<int:email_id>`
**Auth**: `login_required`

Dettaglio comunicazione.

**Status**: 200, 404

### `POST /api/emails`
**Auth**: `role_required("admin", "operatore")`

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

**Status**: 201, 400

### `PATCH /api/emails/<int:email_id>`
**Auth**: `role_required("admin", "operatore")`

Aggiornamento parziale.

**Status**: 200, 400, 404

### `DELETE /api/emails/<int:email_id>`
**Auth**: `role_required("admin", "operatore")`

Elimina comunicazione.

**Status**: 200, 404

## Tasks

### `GET /api/tasks`
**Auth**: `login_required`

Elenco tutte le task.

**Status**: 200

### `GET /api/tasks/<int:task_id>`
**Auth**: `login_required`

Dettaglio task.

**Status**: 200, 404

### `POST /api/tasks`
**Auth**: `role_required("admin", "operatore")`

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
  "lavoro_id": null
}
```

**Status**: 201, 400

### `PATCH /api/tasks/<int:task_id>`
**Auth**: `role_required("admin", "operatore")`

Aggiornamento parziale task.

**Status**: 200, 400, 404

### `DELETE /api/tasks/<int:task_id>`
**Auth**: `role_required("admin", "operatore")`

Annulla task (imposta status="annullata", non elimina fisicamente).

**Status**: 200, 404

## Calendar Events

### `GET /api/calendar/events`
**Auth**: `login_required`

Elenco eventi calendario + scadenze task (merged, sorted by start_datetime).

**Status**: 200

### `GET /api/calendar/events/<int:event_id>`
**Auth**: `login_required`

Dettaglio evento.

**Status**: 200, 404

### `POST /api/calendar/events`
**Auth**: `role_required("admin", "operatore")`

Crea evento.

**Body**:
```json
{
  "title": "Riunione",
  "event_type": "appuntamento",
  "start_datetime": "2024-01-15T14:00:00",
  "end_datetime": "2024-01-15T15:00:00",
  "cliente_id": 1
}
```

**Status**: 201, 400

### `PATCH /api/calendar/events/<int:event_id>`
**Auth**: `role_required("admin", "operatore")`

Aggiornamento parziale evento.

**Status**: 200, 400, 404

### `DELETE /api/calendar/events/<int:event_id>`
**Auth**: `role_required("admin", "operatore")`

Elimina evento.

**Status**: 200, 404

## Anagrafiche (Clienti, Lavori, Preventivi)

Tutti gli endpoint sotto questa sezione usano il formato standard `{"success": true, "data": ..., "error": null}`.

### `GET /api/clienti/getall`
**Auth**: `login_required`

Elenco clienti con conteggio lavori.

**Response** `200`:
```json
{
  "success": true,
  "data": [
    {"id": 1, "nome": "...", "telefono": "...", "email": "...", "note": "...", "colore": "...", "count_lavori": 0}
  ],
  "error": null
}
```

**Status**: 200

### `GET /api/clienti/get/<int:cliente_id>`
**Auth**: `login_required`

Dettaglio cliente con lista lavori.

**Status**: 200, 404

### `GET /api/clienti/getid/<string:nome>`
**Auth**: `login_required`

Ottiene ID cliente per nome esatto.

**Response** `200`:
```json
{"success": true, "data": {"id": 1}, "error": null}
```

**Status**: 200, 404

### `GET /api/lavori/getall`
**Auth**: `login_required`

Elenco lavori con dati cliente.

**Status**: 200

### `GET /api/lavori/get/<int:id>`
**Auth**: `login_required`

Dettaglio lavoro.

**Status**: 200, 404

### `GET /api/preventivi/getall`
**Auth**: `login_required`

Elenco preventivi ERP + preventivi PDF esterni (da Lavoro con preventivo_pdf_path). Include righe.

**Status**: 200

### `GET /api/preventivi/get/<int:id>`
**Auth**: `login_required`

Dettaglio preventivo con righe e dati cliente.

**Status**: 200, 404

## Riepilogo endpoint

| Metodo | URL | Auth | Status |
|--------|-----|------|--------|
| GET | `/api/search` | `login_required` | 200 |
| GET | `/api/dashboard/summary` | `login_required` | 200, 500 |
| GET | `/api/finance` | `login_required` | 200 |
| GET | `/api/finance/<id>` | `login_required` | 200, 404 |
| POST | `/api/finance` | admin, operatore | 201, 400 |
| PATCH | `/api/finance/<id>` | admin, operatore | 200, 400, 404 |
| DELETE | `/api/finance/<id>` | admin, operatore | 200, 404 |
| GET | `/api/finance/summary` | `login_required` | 200, 400 |
| GET | `/api/emails` | `login_required` | 200 |
| GET | `/api/emails/<id>` | `login_required` | 200, 404 |
| POST | `/api/emails` | admin, operatore | 201, 400 |
| PATCH | `/api/emails/<id>` | admin, operatore | 200, 400, 404 |
| DELETE | `/api/emails/<id>` | admin, operatore | 200, 404 |
| GET | `/api/tasks` | `login_required` | 200 |
| GET | `/api/tasks/<id>` | `login_required` | 200, 404 |
| POST | `/api/tasks` | admin, operatore | 201, 400 |
| PATCH | `/api/tasks/<id>` | admin, operatore | 200, 400, 404 |
| DELETE | `/api/tasks/<id>` | admin, operatore | 200, 404 |
| GET | `/api/calendar/events` | `login_required` | 200 |
| GET | `/api/calendar/events/<id>` | `login_required` | 200, 404 |
| POST | `/api/calendar/events` | admin, operatore | 201, 400 |
| PATCH | `/api/calendar/events/<id>` | admin, operatore | 200, 400, 404 |
| DELETE | `/api/calendar/events/<id>` | admin, operatore | 200, 404 |
| GET | `/api/clienti/getall` | `login_required` | 200 |
| GET | `/api/clienti/get/<id>` | `login_required` | 200, 404 |
| GET | `/api/clienti/getid/<nome>` | `login_required` | 200, 404 |
| GET | `/api/lavori/getall` | `login_required` | 200 |
| GET | `/api/lavori/get/<id>` | `login_required` | 200, 404 |
| GET | `/api/preventivi/getall` | `login_required` | 200 |
| GET | `/api/preventivi/get/<id>` | `login_required` | 200, 404 |
