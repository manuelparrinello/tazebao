# Tasks list rework

## Obiettivo
Ristrutturare la vista lista task (`/tasks`) con:
- Tab-bar filtri sempre visibile
- Raggruppamento per cliente in sezioni verticali
- Quick-toggle completamento via AJAX (checkbox)
- Task completate visibili solo nella tab dedicata

## Modifiche

### 1. `app/routes/tasks.py` — view `tasks()`

**Cosa cambia:**
- `TASK_FILTERS` diventa: `{"tutte", "aperte", "scadute", "in_scadenza", "completate", "annullate"}`
- Default filter: `"aperte"` (invece di `None` = tutte)
- Aggiunto filtro `"completate"`: `Task.status == "completata"`
- Aggiunto filtro `"annullate"`: `Task.status == "annullata"`
- Rimosso filtro `"urgenti"` (sostituito dalla priorità visibile nelle righe)
- Dopo la query, i task vengono raggruppati per `task.cliente` usando `defaultdict(list)`
- Ogni gruppo ordinato per priorità (urgente→alta→media→bassa) e poi per scadenza
- Gruppi ordinati alfabeticamente per nome cliente
- Task senza cliente vanno in una sezione "Senza cliente"

**Template context** (cambia):
- `tasks_list` → `client_groups` (lista di dict `{"cliente", "tasks", "count"}`) + `no_client_tasks` (lista)
- `active_filter` sempre valorizzato (default `"aperte"`)
- Aggiunto `clienti` per eventuale filtro rapido

**Codice:**

```python
TASK_FILTERS = {"tutte", "aperte", "scadute", "in_scadenza", "completate", "annullate"}
CLOSED_STATUSES = ("completata", "annullata")


@bp.get("/tasks")
@login_required
def tasks():
    filter_name = request.args.get("filter", "").strip().lower()
    if filter_name not in TASK_FILTERS:
        filter_name = "aperte"

    query = Task.query
    today = date.today()

    if filter_name == "aperte":
        query = query.filter(~Task.status.in_(CLOSED_STATUSES))
    elif filter_name == "scadute":
        query = query.filter(
            Task.due_date < today,
            ~Task.status.in_(CLOSED_STATUSES),
        )
    elif filter_name == "in_scadenza":
        query = query.filter(
            Task.due_date >= today,
            Task.due_date <= today + timedelta(days=3),
            ~Task.status.in_(CLOSED_STATUSES),
        )
    elif filter_name == "completate":
        query = query.filter(Task.status == "completata")
    elif filter_name == "annullate":
        query = query.filter(Task.status == "annullata")

    tasks_list = query.order_by(Task.created_at.desc()).all()

    tasks_by_client = defaultdict(list)
    for task in tasks_list:
        tasks_by_client[task.cliente].append(task)

    client_groups = []
    for cliente, group_tasks in tasks_by_client.items():
        if cliente is None:
            continue
        client_groups.append({
            "cliente": cliente,
            "tasks": sorted(group_tasks, key=_priority_sort_key),
            "count": len(group_tasks),
        })
    client_groups.sort(key=lambda g: g["cliente"].name.lower())

    no_client_tasks = sorted(tasks_by_client.get(None, []), key=_priority_sort_key)

    return render_template(
        "tasks.html",
        client_groups=client_groups,
        no_client_tasks=no_client_tasks,
        categories=TASK_CATEGORIES,
        statuses=TASK_STATUSES,
        priorities=TASK_PRIORITIES,
        active_filter=filter_name,
        clienti=Cliente.query.order_by(Cliente.name.asc()).all(),
    )
```

---

### 2. `templates/tasks.html` — riscritta completamente

**Struttura:**

```
┌───────────────────────────────────────────────────┐
│ Header: Task + bottoni (Nuovo, Board)              │
├───────────────────────────────────────────────────┤
│ Tab-bar filtri: [Tutte] [Aperte] [Scadute]        │
│                 [In scadenza] [Completate] [Ann.]  │
├───────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────┐ │
│ │ Cliente: Rossi Mario (3)              [badge] │ │
│ │ ☐ ⬤ Task urgente          31/12  [✏️ 🗑️]      │ │
│ │ ☐ ⬤ Task media            15/01  [✏️ 🗑️]      │ │
│ ├───────────────────────────────────────────────┤ │
│ │ Cliente: Bianchi Luigi (1)            [badge] │ │
│ │ ☐ ⬤ Task altra               -     [✏️ 🗑️]      │ │
│ ├───────────────────────────────────────────────┤ │
│ │ Senza cliente (2)                     [badge] │ │
│ │ ☐ ⬤ Task generica             -     [✏️ 🗑️]      │ │
│ └───────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────┤
│ Mobile: stesse sezioni in mobile-list             │
└───────────────────────────────────────────────────┘
```

**Dettaglio template:**

```html
{% extends "base.html" %}

{% block title %}Task{% endblock %}
{% block content %}
{% set can_mutate = current_user is defined and current_user is not none and current_user.role in ("admin", "operatore") %}
{% set filter_labels = {"tutte": "Tutte", "aperte": "Aperte", "scadute": "Scadute", "in_scadenza": "In scadenza", "completate": "Completate", "annullate": "Annullate"} %}

<div class="row mx-auto w-100 align-items-start g-3">
    <div class="col-12 col-xl-7 px-0">
        <div class="editorial-page-header">
            <h3 class="fw-bolder mb-1">
                <i class="bi bi-list-check me-2 text-primary"></i>Task
            </h3>
            <p class="text-secondary mb-0">Elenco delle task ERP operative.</p>
        </div>
    </div>
    <div class="col-12 col-xl-5 px-0">
        <div class="erp-action-bar justify-content-xl-end">
            {% if can_mutate %}
            <a class="btn btn-primary erp-action-primary" href="{{ url_for('tasks.task_new') }}">
                <i class="bi bi-plus-lg"></i>&nbsp;Nuovo task
            </a>
            {% endif %}
            <a class="btn btn-outline-secondary erp-action-secondary" href="{{ url_for('tasks.tasks_board') }}">
                <i class="bi bi-kanban me-1"></i>&nbsp;Vista board
            </a>
        </div>
    </div>
</div>
<hr>

<!-- Tab-bar filtri -->
<div class="task-filter-tabs mb-4">
    {% for key, label in filter_labels.items() %}
    <a href="{{ url_for('tasks.tasks', filter=key) }}"
       class="task-filter-tab {% if active_filter == key %}active{% endif %}">
        {{ label }}
    </a>
    {% endfor %}
</div>

{% set has_tasks = client_groups or no_client_tasks %}

{% if has_tasks %}
<div class="mt-3">
    <div class="card rounded-3 border border-light-subtle" data-mobile-list-clean>
        <div class="card-body p-0 p-md-4">

            <!-- Desktop: sezioni per cliente -->
            <div class="d-none d-md-block">
                {% for group in client_groups %}
                <div class="task-group">
                    <div class="task-group-header">
                        <div class="task-group-header-left">
                            {% if group.cliente.colore %}
                            <span class="task-group-dot" style="background:{{ group.cliente.colore }}"></span>
                            {% endif %}
                            <span class="task-group-name">{{ group.cliente.name }}</span>
                            <span class="task-group-count">{{ group.count }}</span>
                        </div>
                        <a href="{{ url_for('clienti.client_detail', cliente_id=group.cliente.id) }}" class="task-group-link" title="Vedi cliente">
                            <i class="bi bi-box-arrow-up-right"></i>
                        </a>
                    </div>
                    <table class="table erp-table my-0 tasks-table">
                        <tbody>
                            {% for task in group.tasks %}
                            <tr class="task-row" data-task-id="{{ task.id }}">
                                <td class="col-check text-start">
                                    {% if can_mutate %}
                                    <input type="checkbox" class="task-checkbox" data-task-id="{{ task.id }}"
                                           {% if task.status == 'completata' %}checked{% endif %}>
                                    {% endif %}
                                </td>
                                <td class="col-prio text-start">
                                    {% if task.priority %}
                                    <span class="priority-indicator priority-{{ task.priority }}">
                                        <span class="priority-dot"></span>
                                        <span class="priority-label">{{ task.priority|labelize }}</span>
                                    </span>
                                    {% endif %}
                                </td>
                                <td class="col-title text-start">
                                    <a class="fw-bold a-no-color d-block text-truncate task-name"
                                       href="{{ url_for('tasks.task_edit', task_id=task.id) if can_mutate else '#' }}">
                                        {{ task.name }}
                                    </a>
                                </td>
                                <td class="col-lavoro text-center">
                                    {% if task.lavoro %}
                                    <span class="text-truncate d-block">{{ task.lavoro.descrizione }}</span>
                                    {% else %}
                                    <span class="text-secondary">-</span>
                                    {% endif %}
                                </td>
                                <td class="col-status text-center">{{ erp_badge("task_status", task.status) }}</td>
                                <td class="col-date text-center">
                                    {% if task.due_date %}
                                    <span class="{% if task.due_date < today and task.status not in ('completata', 'annullata') %}text-danger fw-bold{% endif %}">
                                        {{ task.due_date|date_it }}
                                    </span>
                                    {% else %}
                                    <span class="text-secondary">-</span>
                                    {% endif %}
                                </td>
                                <td class="col-actions text-end">
                                    <div class="erp-actions justify-content-end">
                                        {% if can_mutate %}
                                        <a class="btn btn-sm btn-outline-secondary erp-icon-btn"
                                           href="{{ url_for('tasks.task_edit', task_id=task.id) }}" aria-label="Modifica">
                                            <i class="bi bi-pencil"></i>
                                        </a>
                                        <form action="{{ url_for('tasks.task_delete', task_id=task.id) }}"
                                              method="post" class="d-inline"
                                              data-confirm-message="Eliminare questo task?">
                                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                            <button type="submit" class="btn btn-sm btn-outline-danger erp-icon-btn"
                                                    aria-label="Elimina">
                                                <i class="bi bi-trash3"></i>
                                            </button>
                                        </form>
                                        {% endif %}
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endfor %}

                {% if no_client_tasks %}
                <div class="task-group">
                    <div class="task-group-header">
                        <div class="task-group-header-left">
                            <span class="task-group-dot" style="background:#adb5bd"></span>
                            <span class="task-group-name">Senza cliente</span>
                            <span class="task-group-count">{{ no_client_tasks|length }}</span>
                        </div>
                    </div>
                    <table class="table erp-table my-0 tasks-table">
                        <tbody>
                            {% for task in no_client_tasks %}
                            <tr class="task-row" data-task-id="{{ task.id }}">
                                <td class="col-check text-start">
                                    {% if can_mutate %}
                                    <input type="checkbox" class="task-checkbox" data-task-id="{{ task.id }}"
                                           {% if task.status == 'completata' %}checked{% endif %}>
                                    {% endif %}
                                </td>
                                <td class="col-prio text-start">
                                    {% if task.priority %}
                                    <span class="priority-indicator priority-{{ task.priority }}">
                                        <span class="priority-dot"></span>
                                        <span class="priority-label">{{ task.priority|labelize }}</span>
                                    </span>
                                    {% endif %}
                                </td>
                                <td class="col-title text-start">
                                    <a class="fw-bold a-no-color d-block text-truncate task-name"
                                       href="{{ url_for('tasks.task_edit', task_id=task.id) if can_mutate else '#' }}">
                                        {{ task.name }}
                                    </a>
                                </td>
                                <td class="col-lavoro text-center">
                                    {% if task.lavoro %}
                                    <span class="text-truncate d-block">{{ task.lavoro.descrizione }}</span>
                                    {% else %}
                                    <span class="text-secondary">-</span>
                                    {% endif %}
                                </td>
                                <td class="col-status text-center">{{ erp_badge("task_status", task.status) }}</td>
                                <td class="col-date text-center">
                                    {% if task.due_date %}
                                    <span class="{% if task.due_date < today and task.status not in ('completata', 'annullata') %}text-danger fw-bold{% endif %}">
                                        {{ task.due_date|date_it }}
                                    </span>
                                    {% else %}
                                    <span class="text-secondary">-</span>
                                    {% endif %}
                                </td>
                                <td class="col-actions text-end">
                                    <div class="erp-actions justify-content-end">
                                        {% if can_mutate %}
                                        <a class="btn btn-sm btn-outline-secondary erp-icon-btn"
                                           href="{{ url_for('tasks.task_edit', task_id=task.id) }}" aria-label="Modifica">
                                            <i class="bi bi-pencil"></i>
                                        </a>
                                        <form action="{{ url_for('tasks.task_delete', task_id=task.id) }}"
                                              method="post" class="d-inline"
                                              data-confirm-message="Eliminare questo task?">
                                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                            <button type="submit" class="btn btn-sm btn-outline-danger erp-icon-btn"
                                                    aria-label="Elimina">
                                                <i class="bi bi-trash3"></i>
                                            </button>
                                        </form>
                                        {% endif %}
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}
            </div>

            <!-- Mobile -->
            <div class="mobile-list d-md-none">
                {% for group in client_groups %}
                <div class="task-group-mobile">
                    <div class="task-group-header-mobile">
                        {% if group.cliente.colore %}
                        <span class="task-group-dot" style="background:{{ group.cliente.colore }}"></span>
                        {% endif %}
                        <span class="fw-bold">{{ group.cliente.name }}</span>
                        <span class="task-group-count">{{ group.count }}</span>
                    </div>
                    {% for task in group.tasks %}
                    {% set prio = task.priority if task.priority else "unknown" %}
                    <div class="task-row-mobile" data-task-id="{{ task.id }}">
                        <div class="d-flex align-items-start gap-2">
                            {% if can_mutate %}
                            <input type="checkbox" class="task-checkbox mt-1" data-task-id="{{ task.id }}"
                                   {% if task.status == 'completata' %}checked{% endif %}>
                            {% endif %}
                            <div class="min-w-0 flex-grow-1">
                                <a class="mobile-row-link" href="{{ url_for('tasks.task_edit', task_id=task.id) if can_mutate else '#' }}">
                                    <div class="d-flex align-items-center gap-2 mb-1">
                                        <span class="priority-indicator priority-{{ prio }}"><span class="priority-dot"></span></span>
                                        <span class="fw-bold mobile-row-title">{{ task.name }}</span>
                                    </div>
                                    <div class="mobile-row-meta">
                                        <span class="mobile-row-muted">{{ erp_badge("task_status", task.status) }}</span>
                                        {% if task.due_date %}
                                        <span class="mobile-row-muted">
                                            <i class="bi bi-calendar3 me-1"></i>{{ task.due_date|date_it }}
                                        </span>
                                        {% endif %}
                                        {% if task.lavoro %}
                                        <span class="mobile-row-muted">
                                            <i class="bi bi-briefcase me-1"></i>{{ task.lavoro.descrizione }}
                                        </span>
                                        {% endif %}
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
                {% if no_client_tasks %}
                <div class="task-group-mobile">
                    <div class="task-group-header-mobile">
                        <span class="task-group-dot" style="background:#adb5bd"></span>
                        <span class="fw-bold">Senza cliente</span>
                        <span class="task-group-count">{{ no_client_tasks|length }}</span>
                    </div>
                    {% for task in no_client_tasks %}
                    {% set prio = task.priority if task.priority else "unknown" %}
                    <div class="task-row-mobile" data-task-id="{{ task.id }}">
                        <div class="d-flex align-items-start gap-2">
                            {% if can_mutate %}
                            <input type="checkbox" class="task-checkbox mt-1" data-task-id="{{ task.id }}"
                                   {% if task.status == 'completata' %}checked{% endif %}>
                            {% endif %}
                            <div class="min-w-0 flex-grow-1">
                                <a class="mobile-row-link" href="{{ url_for('tasks.task_edit', task_id=task.id) if can_mutate else '#' }}">
                                    <div class="d-flex align-items-center gap-2 mb-1">
                                        <span class="priority-indicator priority-{{ prio }}"><span class="priority-dot"></span></span>
                                        <span class="fw-bold mobile-row-title">{{ task.name }}</span>
                                    </div>
                                    <div class="mobile-row-meta">
                                        <span class="mobile-row-muted">{{ erp_badge("task_status", task.status) }}</span>
                                        {% if task.due_date %}
                                        <span class="mobile-row-muted">
                                            <i class="bi bi-calendar3 me-1"></i>{{ task.due_date|date_it }}
                                        </span>
                                        {% endif %}
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>

        </div>
    </div>
</div>
{% else %}
<div class="mt-5">
    <div class="card rounded-3 border border-light-subtle">
        <div class="card-body p-4">
            <div class="editorial-empty-state">
                <div class="editorial-empty-icon">
                    <i class="bi bi-inbox"></i>
                </div>
                <div class="editorial-empty-body">
                    <h6 class="fw-bolder mb-1">Nessun task trovato</h6>
                    <p class="text-secondary mb-3 small">
                        {% if active_filter == "completate" %}Nessun task completato.
                        {% elif active_filter == "annullate" %}Nessun task annullato.
                        {% elif active_filter == "scadute" %}Nessun task scaduto. Bene!
                        {% elif active_filter == "in_scadenza" %}Nessun task in scadenza.
                        {% else %}Non ci sono task ERP presenti. Creane uno nuovo per iniziare.
                        {% endif %}
                    </p>
                    {% if can_mutate and active_filter not in ("completate", "annullate") %}
                    <a class="btn btn-sm btn-outline-primary" href="{{ url_for('tasks.task_new') }}">
                        <i class="bi bi-plus-lg me-1"></i>Nuovo task
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endif %}
{% endblock %}

{% block scripts %}
{{ super() }}
<script src="{{ url_for('static', filename='js/tasks-list.js') }}"></script>
{% endblock %}
```

Note sul template:
- Rimosso il badge "Filtro attivo" in favore della tab-bar
- Colonna "Cliente" rimossa dalla tabella (sostituita dal raggruppamento)
- Aggiunta colonna "check" con checkbox per quick-toggle
- `today` passato al template per colorare scadenze passate
- `filter_labels` per i nomi delle tab
- Script `tasks-list.js` caricato alla fine

---

### 3. `static/js/tasks-list.js` — nuovo file

```javascript
(function () {
  'use strict'

  var checkboxes = document.querySelectorAll('.task-checkbox')
  if (!checkboxes.length) return

  checkboxes.forEach(function (cb) {
    cb.addEventListener('change', function () {
      var taskId = this.dataset.taskId
      if (!taskId) return

      var newStatus = this.checked ? 'completata' : 'da_fare'

      fetch('/api/tasks/' + taskId, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ status: newStatus }),
      })
        .then(function (r) { return r.json() })
        .then(function (res) {
          if (res.success === false) {
            throw new Error(res.error || 'Errore aggiornamento task')
          }
          showFeedback('success', newStatus === 'completata' ? 'Task completata' : 'Task riaperta')
        })
        .catch(function (err) {
          console.error('[tasks-list]', err)
          showFeedback('error', err.message || 'Errore durante l\'aggiornamento')
          cb.checked = !cb.checked
        })
    })
  })

  function getCsrfToken() {
    var el = document.querySelector('input[name="csrf_token"]')
    return el ? el.value : ''
  }

  function showFeedback(type, msg) {
    var container = document.querySelector('.erp-toast-container')
    if (!container) {
      container = document.createElement('div')
      container.className = 'erp-toast-container position-fixed bottom-0 end-0 p-3'
      document.body.appendChild(container)
    }
    var toast = document.createElement('div')
    toast.className = 'toast align-items-center text-bg-' + (type === 'success' ? 'success' : 'danger') + ' border-0'
    toast.setAttribute('role', 'alert')
    toast.innerHTML = '<div class="d-flex">' +
      '<div class="toast-body">' + escapeHtml(msg) + '</div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
      '</div>'
    container.appendChild(toast)
    var bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 2500 })
    bsToast.show()
    toast.addEventListener('hidden.bs.toast', function () { toast.remove() })
  }
})()
```

---

### 4. `static/css/style.css` — aggiunte in fondo (prima della pagination)

```css

/* =========================
   TASK LIST REWORK
========================= */

/* Filter tabs */
.task-filter-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.task-filter-tab {
  display: inline-flex;
  align-items: center;
  padding: 0.4rem 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 999px;
  border: 1px solid var(--app-border);
  color: var(--app-text);
  text-decoration: none !important;
  background: transparent;
  transition: all 0.15s ease;
}
.task-filter-tab:hover {
  background: var(--app-light-bg);
  border-color: var(--app-primary);
  color: var(--app-primary);
}
.task-filter-tab.active {
  background: var(--app-primary);
  border-color: var(--app-primary);
  color: #fff;
}

/* Task group sections */
.task-group {
  margin-bottom: 1.5rem;
}
.task-group:last-child {
  margin-bottom: 0;
}
.task-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.75rem;
  margin-bottom: 0.35rem;
  border-radius: 8px;
  background: var(--app-light-bg);
  border-left: 4px solid var(--app-primary);
}
.task-group-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}
.task-group-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.task-group-name {
  font-weight: 700;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-group-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 0.4rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  background: rgba(0,0,0,0.08);
  color: var(--app-text-muted);
}
.task-group-link {
  color: var(--app-text-muted);
  font-size: 0.8rem;
  text-decoration: none !important;
  flex-shrink: 0;
}
.task-group-link:hover {
  color: var(--app-primary);
}

/* Task rows */
.task-row td {
  vertical-align: middle;
  padding-top: 0.55rem;
  padding-bottom: 0.55rem;
}
.task-row .task-name {
  color: var(--app-text);
}
.task-row .task-name:hover {
  color: var(--app-primary);
}
.col-check {
  width: 36px;
  padding-right: 0 !important;
}
.col-lavoro {
  width: 130px;
}

/* Checkbox personalizzata */
.task-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--app-primary);
}

/* Mobile groups */
.task-group-mobile {
  margin-bottom: 1rem;
}
.task-group-header-mobile {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.85rem;
  background: var(--app-light-bg);
  border-left: 4px solid var(--app-primary);
  border-radius: 0;
}
.task-row-mobile {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--app-border);
}
.task-row-mobile:last-child {
  border-bottom: none;
}
```

Aggiungere queste regole PRIMA del blocco `/* ========================= PAGINATION (ERP) ========================= */` (linea 5277).

---

### 5. `app/routes/tasks.py` — aggiungere `today` al context del template

Aggiungere `"today": today` nel dict passato a `render_template`.

---

### Nessuna modifica a
- Modello `Task`
- API `PATCH /api/tasks/<id>` (già funzionante)
- Vista kanban (`tasks_board.html`)
- Vista form (`task_form.html`)
- Altre blueprint

## Verifica

Dopo l'implementazione:
1. Visitare `/tasks` — deve mostrare la tab-bar con "Aperte" selezionato di default
2. Cliccare ogni tab — deve filtrare correttamente
3. Verificare gruppi cliente con header colorato
4. Cliccare checkbox — task deve completarsi/riaprirsi via AJAX
5. Vista mobile — gruppi cliente devono essere preservati
6. Visitare `/tasks?filter=tutte` — deve mostrare tutti i task (inclusi completati/annullati)
