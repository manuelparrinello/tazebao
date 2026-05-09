/*--------------------*/
/*  CANCELLA CLIENTE  */
/*--------------------*/
function getCSRFToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || "";
}

function csrfHeaders(headers = {}) {
  const token = getCSRFToken();
  return token ? { ...headers, "X-CSRFToken": token } : headers;
}

function parseDateLike(value) {
  if (!value) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  if (typeof value === "number") {
    const parsedNumber = new Date(value);
    return Number.isNaN(parsedNumber.getTime()) ? null : parsedNumber;
  }

  const text = String(value).trim();
  if (!text) return null;

  const dateOnlyMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (dateOnlyMatch) {
    const [, year, month, day] = dateOnlyMatch;
    const parsedDateOnly = new Date(Number(year), Number(month) - 1, Number(day));
    return Number.isNaN(parsedDateOnly.getTime()) ? null : parsedDateOnly;
  }

  const normalized = text.includes("T") ? text : text.replace(" ", "T");
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function capitalizeFirstLetter(value) {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatItalianDate(value) {
  const parsed = parseDateLike(value);
  if (!parsed) return "-";

  const parts = new Intl.DateTimeFormat("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).formatToParts(parsed);

  return parts
    .map((part) => {
      if (part.type !== "month") return part.value;
      return capitalizeFirstLetter(part.value);
    })
    .join("");
}

function formatItalianDateTime(value) {
  const parsed = parseDateLike(value);
  if (!parsed) return "-";

  const datePart = formatItalianDate(parsed);
  const timePart = new Intl.DateTimeFormat("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);

  return `${datePart} ${timePart}`;
}

window.erpDateFormatter = {
  formatDate: formatItalianDate,
  formatDateTime: formatItalianDateTime,
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeBadgeValue(value) {
  if (value === null || value === undefined) return "";
  return String(value).trim().toLowerCase().replaceAll(" ", "_");
}

const ERP_BADGE_MAP = {
  work_status: {
    completato: ["success", "Completato"],
    completata: ["success", "Completato"],
    in_corso: ["primary", "In corso"],
    in_attesa: ["warning", "In attesa"],
    da_iniziare: ["secondary", "Da iniziare"],
    annullata: ["secondary", "Annullata"],
  },
  work_priority: {
    urgente: ["danger", "Urgente"],
    alta: ["danger", "Alta"],
    media: ["warning", "Media"],
    bassa: ["success", "Bassa"],
  },
  task_status: {
    da_fare: ["primary", "Da fare"],
    in_corso: ["primary", "In corso"],
    in_revisione: ["warning", "In revisione"],
    completata: ["success", "Completata"],
    annullata: ["secondary", "Annullata"],
  },
  task_priority: {
    urgente: ["danger", "Urgente"],
    alta: ["danger", "Alta"],
    media: ["warning", "Media"],
    bassa: ["success", "Bassa"],
  },
  task_category: {
    social_media: ["text-bg-light border", "Social media"],
    grafica: ["text-bg-light border", "Grafica"],
    amministrazione: ["text-bg-light border", "Amministrazione"],
    fotografia: ["text-bg-light border", "Fotografia"],
    web: ["text-bg-light border", "Web"],
    commerciale: ["text-bg-light border", "Commerciale"],
    generale: ["text-bg-light border", "Generale"],
  },
  quote_status: {
    bozza: ["warning", "Bozza"],
    draft: ["warning", "Bozza"],
    inviato: ["primary", "Inviato"],
    inviata: ["primary", "Inviato"],
    accettato: ["success", "Accettato"],
    accettata: ["success", "Accettato"],
    approvato: ["success", "Accettato"],
    approvata: ["success", "Accettato"],
    rifiutato: ["danger", "Rifiutato"],
    rifiutata: ["danger", "Rifiutato"],
    annullato: ["secondary", "Annullato"],
    annullata: ["secondary", "Annullato"],
  },
  event_type: {
    appuntamento: ["primary", "Appuntamento"],
    scadenza: ["warning", "Scadenza"],
    impegno_cliente: ["info", "Impegno cliente"],
    promemoria: ["secondary", "Promemoria"],
    generale: ["text-bg-light border", "Generale"],
    task_due_date: ["warning", "Task"],
  },
  finance_income_status: {
    effettiva: ["success", "Entrata effettiva"],
    prevista: ["warning", "Entrata prevista"],
  },
  finance_expense_type: {
    fissa: ["secondary", "Fissa"],
    variabile: ["warning", "Variabile"],
  },
  finance_category: {
    pagamento_cliente: ["text-bg-light border", "Pagamento cliente"],
    fornitore: ["text-bg-light border", "Fornitore"],
    software: ["text-bg-light border", "Software"],
    advertising: ["text-bg-light border", "Advertising"],
    consulenza: ["text-bg-light border", "Consulenza"],
    attrezzatura: ["text-bg-light border", "Attrezzatura"],
    tasse: ["text-bg-light border", "Tasse"],
    stipendio: ["text-bg-light border", "Stipendio"],
    commercialista: ["text-bg-light border", "Commercialista"],
    banca: ["text-bg-light border", "Banca"],
    costituzione_societa: ["text-bg-light border", "Costituzione società"],
    generale: ["text-bg-light border", "Generale"],
  },
  finance_movement_type: {
    entrata: ["success", "Entrata"],
    uscita: ["danger", "Uscita"],
  },
  mail_read_status: {
    read: ["success", "Letta"],
    unread: ["warning", "Non letta"],
    inviata: ["primary", "Inviata"],
  },
  mail_direction: {
    inbound: ["info", "Ricevuta"],
    outbound: ["success", "Inviata"],
  },
  user_role: {
    admin: ["primary", "Admin"],
    operatore: ["primary", "Operatore"],
    readonly: ["secondary", "Readonly"],
  },
  user_state: {
    active: ["success", "Attivo"],
    inactive: ["secondary", "Non attivo"],
  },
};

function erpBadgePayload(kind, value) {
  const key = normalizeBadgeValue(value);
  return ERP_BADGE_MAP[kind]?.[key] || null;
}

function erpBadgeLabel(kind, value, text = null) {
  const payload = erpBadgePayload(kind, value);
  if (payload) return text || payload[1];
  if (text) return text;
  if (value === null || value === undefined || value === "") return "-";
  return String(value).replaceAll("_", " ").replaceAll("-", " ").replace(/\s+/g, " ").trim().replace(/\b\w/g, (char) => char.toUpperCase());
}

function erpBadgeHtml(kind, value, text = null) {
  const payload = erpBadgePayload(kind, value);
  const normalizedVariants = {
    primary: "text-bg-primary",
    success: "text-bg-success",
    warning: "text-bg-warning",
    danger: "text-bg-danger",
    info: "text-bg-info",
    secondary: "text-bg-secondary",
  };
  const rawVariant = payload ? payload[0] : "text-bg-light border";
  const variant = normalizedVariants[rawVariant] || rawVariant;
  const label = escapeHtml(erpBadgeLabel(kind, value, text));
  return `<span class="badge rounded-pill erp-badge ${variant}">${label}</span>`;
}

window.erpBadge = {
  payload: erpBadgePayload,
  label: erpBadgeLabel,
  html: erpBadgeHtml,
};

function deleteCliente(id) {
  return fetch(`/clienti/${id}`, {
    method: "delete",
    headers: csrfHeaders({
      Accept: "application/json",
    }),
  });
}

async function clickForDeleteCliente(event, idCliente) {
  event.preventDefault();
  const utenteConferma = confirm("Sei sicuro di voler cancellare il cliente?");

  if (utenteConferma === false) {
    return;
  }

  try {
    const response = await deleteCliente(idCliente);
    console.log("DELETE status:", response.status);
    if (response.ok === false) {
      const corpoRispostaComeTesto = await response.text();
      console.error("Errore response:", corpoRispostaComeTesto);
      throw new Error(
        `Errore durante l'eliminazione (HTTP ${response.status})`
      );
    }
    alert("Cliente eliminato con successo!");
    window.location.href = "/clienti";
  } catch (errore) {
    alert(errore.message);
    console.error(errore);
  }
}

/*-------------------*/
/*  CANCELLA LAVORO  */
/*-------------------*/

function deleteLavoro(id) {
  return fetch(`/lavori/${id}`, {
    method: "delete",
    headers: csrfHeaders({
      Accept: "application/json",
    }),
  });
}

async function clickForDeleteLavoro(event, idLavoro) {
  event.preventDefault();
  const conferma = confirm("Vuoi cancellare questo lavoro?");
  if (!conferma) return;

  try {
    const response = await deleteLavoro(idLavoro);
    if (!response) {
      const corpoRispostaTesto = await response.text();
      console.error("Errore response:", corpoRispostaTesto);
      throw new Error(
        `Errore durante l'eliminazione (HTTP ${response.status})`
      );
    }
    window.alert("Lavoro eliminato con successo!");
    window.location.href = "/lavori";
  } catch (errore) {
    alert(errore.message);
    console.error(errore);
  }
}

if (document.getElementById("app")) {
  const erpDashboardApp = Vue.createApp({
    delimiters: ["[[", "]]"],
    data() {
      return {
        loading: true,
        error: null,
        summary: null,
      };
    },
    computed: {
      kpiCards() {
        if (!this.summary) return [];
        return [
          { title: "Task aperte", value: this.summary.task_open_count, icon: "bi-list-check" },
          { title: "Scadenze prossime", value: this.summary.task_due_soon_count, icon: "bi-alarm" },
          { title: "Task scadute", value: this.summary.overdue_task_count, icon: "bi-exclamation-triangle" },
          { title: "Email non lette", value: this.summary.unread_mail_count, icon: "bi-envelope-exclamation" },
          { title: "Eventi prossimi", value: this.summary.upcoming_events_count, icon: "bi-calendar-event" },
          { title: "Clienti", value: this.summary.active_clients_count, icon: "bi-people" },
          { title: "Lavori attivi", value: this.summary.active_jobs_count, icon: "bi-briefcase" },
          { title: "Preventivi bozza", value: this.summary.draft_quotes_count, icon: "bi-file-earmark-text" },
          { title: "Preventivi accettati", value: this.summary.accepted_quotes_count, icon: "bi-check2-circle" },
        ];
      },
      financeCards() {
        if (!this.summary) return [];
        return [
          { title: "In cassa", value: this.formatCurrency(this.summary.current_balance), icon: "bi-cash-coin" },
          { title: "Entrate effettive mese", value: this.formatCurrency(this.summary.month_income_effective), icon: "bi-arrow-down-circle" },
          { title: "Entrate previste mese", value: this.formatCurrency(this.summary.month_income_expected), icon: "bi-clock-history" },
          { title: "Uscite mese", value: this.formatCurrency(this.summary.month_expenses_total), icon: "bi-arrow-up-circle" },
          { title: "Spese fisse", value: this.formatCurrency(this.summary.month_expenses_fixed), icon: "bi-pin-angle" },
          { title: "Spese variabili", value: this.formatCurrency(this.summary.month_expenses_variable), icon: "bi-shuffle" },
          { title: "Bilancio mese", value: this.formatCurrency(this.summary.month_balance), icon: "bi-graph-up" },
        ];
      },
    },
    mounted() {
      this.loadDashboard();
    },
    methods: {
      async loadDashboard() {
        this.loading = true;
        this.error = null;

        try {
          const response = await fetch("/api/dashboard/summary", {
            headers: { Accept: "application/json" },
          });
          const payload = await response.json();

          if (!response.ok || payload.success === false) {
            throw new Error(payload.error || "Errore caricamento dashboard");
          }

          this.summary = payload.data;
        } catch (errore) {
          this.error = errore.message;
        } finally {
          this.loading = false;
        }
      },
      formatDate(value) {
        return formatItalianDate(value);
      },
      formatDateTime(value) {
        return formatItalianDateTime(value);
      },
      formatCurrency(value) {
        if (value === null || value === undefined) return "-";
        return new Intl.NumberFormat("it-IT", {
          style: "currency",
          currency: "EUR",
        }).format(value);
      },
      labelize(value) {
        if (!value) return "-";
        return value.replaceAll("_", " ");
      },
      badgeHtml(kind, value, text) {
        const html = window.erpBadge?.html(kind, value, text);
        return html || `<span class="badge rounded-pill erp-badge text-bg-light border">${window.erpBadge?.label(kind, value, text) || value || '-'}</span>`;
      },
    },
    template: `
      <section class="container-fluid px-0">
        <div class="d-flex flex-column flex-lg-row align-items-lg-center justify-content-between gap-3 mb-4">
          <div>
            <p class="text-primary text-uppercase small fw-bold mb-2">Dashboard ERP</p>
            <h1 class="h3 mb-2">Panoramica operativa</h1>
            <p class="text-secondary mb-0">KPI aggiornati da task, calendario, clienti, lavori e preventivi.</p>
          </div>
          <button class="btn btn-outline-primary" type="button" @click="loadDashboard" :disabled="loading">
            <i class="bi bi-arrow-clockwise"></i>&nbsp;Aggiorna
          </button>
        </div>

        <div v-if="loading" class="d-flex align-items-center justify-content-center dashboard-loading">
          <span class="loader"></span>
        </div>

        <div v-else-if="error" class="alert alert-danger d-flex align-items-center justify-content-between gap-3">
          <span>[[ error ]]</span>
          <button class="btn btn-sm btn-outline-danger" type="button" @click="loadDashboard">Riprova</button>
        </div>

        <div v-else>
          <div class="row g-3">
            <div class="col-12 col-md-6 col-xl-3" v-for="card in kpiCards" :key="card.title">
              <article class="card h-100 rounded-3 border border-light-subtle">
                <div class="card-body p-4">
                  <div class="d-flex align-items-start justify-content-between gap-3">
                    <div class="min-w-0">
                      <p class="text-secondary small mb-2">[[ card.title ]]</p>
                      <div class="display-6 fw-bold text-truncate">[[ card.value ]]</div>
                    </div>
                    <div class="dashboard-icon-box rounded-3 bg-primary d-inline-flex align-items-center justify-content-center flex-shrink-0">
                      <i class="bi" :class="card.icon"></i>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div class="mt-4">
            <div class="d-flex align-items-center justify-content-between mb-3">
              <h2 class="h5 mb-0">Finanze</h2>
              <a class="btn btn-sm btn-outline-primary" href="/finance">Apri finanze</a>
            </div>
            <div class="row g-3">
              <div class="col-12 col-md-6 col-xl-3" v-for="card in financeCards" :key="card.title">
                <article class="card h-100 rounded-3 border border-light-subtle">
                  <div class="card-body p-4">
                    <div class="d-flex align-items-start justify-content-between gap-3">
                      <div class="min-w-0">
                        <p class="text-secondary small mb-2">[[ card.title ]]</p>
                        <div class="h3 fw-bold mb-0 text-truncate">[[ card.value ]]</div>
                      </div>
                      <div class="dashboard-icon-box rounded-3 bg-primary d-inline-flex align-items-center justify-content-center flex-shrink-0">
                        <i class="bi" :class="card.icon"></i>
                      </div>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </div>

          <div class="row g-3 mt-3">
            <div class="col-12 col-xl-4">
              <article class="card h-100 rounded-3 border border-light-subtle">
                <div class="card-body p-4">
                  <h2 class="h5 mb-3">Prossimi eventi</h2>
                  <div v-if="summary.upcoming_events.length === 0" class="text-secondary py-3 text-center">
                    <i class="bi bi-calendar2-week d-block fs-2 text-secondary mb-2"></i>
                    <span>Nessun evento nei prossimi 7 giorni.</span>
                  </div>
                  <a v-for="event in summary.upcoming_events" :key="event.id" :href="event.url" class="dashboard-list-item">
                    <div class="d-flex align-items-start justify-content-between gap-2 mb-1">
                      <div class="fw-bold text-truncate min-w-0">[[ event.title ]]</div>
                      <span v-html="badgeHtml('event_type', event.event_type)" class="flex-shrink-0"></span>
                    </div>
                    <div class="small text-secondary d-flex flex-wrap gap-2">
                      <span><i class="bi bi-calendar3 me-1"></i>[[ formatDateTime(event.start_datetime) ]]</span>
                      <span v-if="event.cliente"><i class="bi bi-person me-1"></i>[[ event.cliente.name ]]</span>
                    </div>
                  </a>
                </div>
              </article>
            </div>

            <div class="col-12 col-xl-4">
              <article class="card h-100 rounded-3 border border-light-subtle">
                <div class="card-body p-4">
                  <h2 class="h5 mb-3">Task recenti</h2>
                  <div v-if="summary.recent_tasks.length === 0" class="text-secondary py-3 text-center">
                    <i class="bi bi-list-check d-block fs-2 text-secondary mb-2"></i>
                    <span>Nessuna task presente.</span>
                  </div>
                  <a v-for="task in summary.recent_tasks" :key="task.id" :href="task.url" class="dashboard-list-item">
                    <div class="d-flex align-items-start justify-content-between gap-2 mb-1">
                      <div class="fw-bold text-truncate min-w-0">[[ task.name ]]</div>
                      <span v-html="badgeHtml('task_status', task.status)" class="flex-shrink-0"></span>
                    </div>
                    <div class="small text-secondary d-flex flex-wrap gap-2">
                      <span v-if="task.due_date"><i class="bi bi-calendar3 me-1"></i>Scadenza: [[ formatDate(task.due_date) ]]</span>
                      <span><i class="bi bi-flag me-1"></i>[[ labelize(task.priority) ]]</span>
                    </div>
                  </a>
                </div>
              </article>
            </div>

            <div class="col-12 col-xl-4">
              <article class="card h-100 rounded-3 border border-light-subtle">
                <div class="card-body p-4">
                  <h2 class="h5 mb-3">Preventivi recenti</h2>
                  <div v-if="summary.recent_quotes.length === 0" class="text-secondary py-3 text-center">
                    <i class="bi bi-file-earmark-text d-block fs-2 text-secondary mb-2"></i>
                    <span>Nessun preventivo presente.</span>
                  </div>
                  <a v-for="quote in summary.recent_quotes" :key="quote.id" :href="quote.url" class="dashboard-list-item">
                    <div class="d-flex align-items-start justify-content-between gap-2 mb-1">
                      <div class="fw-bold text-truncate min-w-0">[[ quote.descrizione ]]</div>
                      <span v-html="badgeHtml('quote_status', quote.stato)" class="flex-shrink-0"></span>
                    </div>
                    <div class="small text-secondary d-flex flex-wrap gap-2">
                      <span v-if="quote.cliente"><i class="bi bi-person me-1"></i>[[ quote.cliente.name ]]</span>
                      <span><i class="bi bi-calendar3 me-1"></i>[[ formatDate(quote.data_creazione) ]]</span>
                      <span class="fw-bold">[[ formatCurrency(quote.totale_preventivo) ]]</span>
                    </div>
                  </a>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>
    `,
  });

  erpDashboardApp.mount("#app");
}

