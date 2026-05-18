/*--------------------*/
/*  CANCELLA CLIENTE  */
/*--------------------*/
function getCSRFToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || "";
}

function csrfHeaders(headers = {}) {
  const token = getCSRFToken();
  const base = token ? { ...headers, "X-CSRFToken": token } : headers;
  return { ...base, "X-Requested-With": "XMLHttpRequest" };
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
  editorial_status: {
    idea: ["text-bg-light border", "Idea"],
    da_produrre: ["secondary", "Da produrre"],
    in_revisione: ["warning", "In revisione"],
    approvato: ["success", "Approvato"],
    programmato: ["primary", "Programmato"],
    pubblicato: ["primary", "Pubblicato"],
    annullato: ["secondary", "Annullato"],
  },
  editorial_client_approval: {
    da_approvare: ["warning", "Da approvare"],
    approvato: ["success", "Approvato"],
    modifiche_richieste: ["danger", "Modifiche richieste"],
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
  if (!await erpConfirm("Sei sicuro di voler cancellare il cliente?")) {
    return;
  }

  try {
    const response = await deleteCliente(idCliente);
    console.log("DELETE status:", response.status);
    if (response.ok === false) {
      var errData;
      try { errData = await response.json(); } catch (_) { errData = null; }
      var msg = errData && errData.message ? errData.message : `Errore HTTP ${response.status}`;
      throw new Error(msg);
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
  if (!await erpConfirm("Vuoi cancellare questo lavoro?")) return;

  try {
    const response = await deleteLavoro(idLavoro);
    if (!response.ok) {
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
        const open = this.summary.open_task_count || 0;
        const overdue = this.summary.overdue_task_count || 0;
        const activeJobs = this.summary.active_jobs_count || 0;
        const pendingQuotes = this.summary.pending_quotes_count || 0;
        const upcomingPubs = this.summary.upcoming_publications_count || 0;
        const expectedIncomeCount = this.summary.expected_income_count || 0;
        const expectedIncomeSum = this.summary.expected_income_sum || 0;
        return [
          { title: "Task aperte", value: open, icon: "bi-list-check", valueClass: "", boxClass: "dashboard-icon-box-primary", url: "/tasks" },
          { title: "Task urgenti", value: overdue, icon: "bi-exclamation-triangle", valueClass: overdue > 0 ? "dashboard-kpi-danger" : "", boxClass: overdue > 0 ? "dashboard-icon-box-danger" : "dashboard-icon-box-primary", url: "/tasks" },
          { title: "Lavori attivi", value: activeJobs, icon: "bi-briefcase", valueClass: "", boxClass: "dashboard-icon-box-primary", url: "/lavori" },
          { title: "Preventivi in attesa", value: pendingQuotes, icon: "bi-file-earmark-text", valueClass: pendingQuotes > 0 ? "dashboard-kpi-warning" : "", boxClass: pendingQuotes > 0 ? "dashboard-icon-box-warning" : "dashboard-icon-box-primary", url: "/preventivi" },
          { title: "Pubblicazioni imminenti", value: upcomingPubs, icon: "bi-calendar2-week", valueClass: upcomingPubs > 0 ? "dashboard-kpi-success" : "", boxClass: upcomingPubs > 0 ? "dashboard-icon-box-success" : "dashboard-icon-box-primary", url: "/editorial-calendar" },
          { title: "Entrate previste", value: this.formatCurrency(expectedIncomeSum), icon: "bi-currency-euro", valueClass: expectedIncomeSum > 0 ? "dashboard-kpi-success" : "", boxClass: expectedIncomeSum > 0 ? "dashboard-icon-box-success" : "dashboard-icon-box-primary", url: "/finance" },
        ];
      },
      financeCards() {
        if (!this.summary) return [];
        const bal = this.summary.month_balance || 0;
        return [
          { title: "Bilancio mese", value: this.formatCurrency(bal), icon: "bi-graph-up", valueClass: bal >= 0 ? "text-success" : "text-danger", boxClass: bal >= 0 ? "dashboard-icon-box-success" : "dashboard-icon-box-danger" },
          { title: "Entrate effettive", value: this.formatCurrency(this.summary.month_income_effective || 0), icon: "bi-arrow-down-circle", valueClass: "text-success", boxClass: "dashboard-icon-box-success" },
          { title: "Uscite mese", value: this.formatCurrency(this.summary.month_expenses_total || 0), icon: "bi-arrow-up-circle", valueClass: "text-danger", boxClass: "dashboard-icon-box-danger" },
          { title: "Lavori attivi", value: this.summary.active_jobs_count || 0, icon: "bi-briefcase", valueClass: "", boxClass: "dashboard-icon-box-primary" },
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
          const contentType = response.headers.get("content-type") || "";
          if (!contentType.includes("application/json")) {
            const text = await response.text();
            throw new Error("Il server ha risposto con HTML (possibile errore DB o migration mancante).");
          }
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
        return erpBadgeHtml(kind, value, text);
      },
      priorityHtml(prio) {
        if (!prio) return '<span class="text-secondary">-</span>';
        const label = String(prio).replace(/\b\w/g, c => c.toUpperCase());
        return `<span class="dashboard-list-priority priority-${prio.toLowerCase()}"><span class="priority-dot"></span><span class="priority-label">${label}</span></span>`;
      },
      isOverdue(dateStr) {
        if (!dateStr) return false;
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return d < today;
      },
    },
    template: `
      <section class="container-fluid px-0">
        <div class="d-flex flex-column flex-lg-row align-items-lg-center justify-content-between gap-3 mb-4">
          <div>
            <p class="text-primary text-uppercase small fw-bold mb-2">Dashboard ERP</p>
            <h1 class="h3 mb-2">Panoramica operativa</h1>
            <p class="text-secondary mb-0">Panoramica operativa di oggi.</p>
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
            <div class="col-6 col-md-4 col-xl-2" v-for="card in kpiCards" :key="card.title">
              <a :href="card.url" class="text-decoration-none">
                <article class="card h-100 rounded-3 border border-light-subtle dashboard-kpi-card">
                  <div class="card-body p-3 p-xl-4">
                    <div class="d-flex align-items-center justify-content-between gap-2">
                      <div class="min-w-0">
                        <p class="text-secondary small mb-1 dashboard-kpi-label">[[ card.title ]]</p>
                        <div class="fw-bold dashboard-kpi-value" :class="card.valueClass">[[ card.value ]]</div>
                      </div>
                      <div class="dashboard-icon-box rounded-3 d-inline-flex align-items-center justify-content-center flex-shrink-0" :class="card.boxClass">
                        <i class="bi" :class="card.icon"></i>
                      </div>
                    </div>
                  </div>
                </article>
              </a>
            </div>
          </div>

          <div v-if="summary.today_items && summary.today_items.length > 0" class="mt-4">
            <div class="d-flex align-items-center gap-2 mb-3">
              <h2 class="h5 mb-0">Da fare oggi</h2>
              <span class="badge rounded-pill text-bg-primary erp-badge" v-if="summary.today_items.length">[[ summary.today_items.length ]]</span>
            </div>
            <div class="card rounded-3 border border-light-subtle">
              <div class="card-body p-3 p-md-4">
                <div class="row g-2">
                  <div class="col-12 col-md-6" v-for="item in summary.today_items" :key="item.url + item.label">
                    <a :href="item.url" class="dashboard-today-item">
                      <div class="d-flex align-items-start gap-3">
                        <div class="dashboard-today-icon flex-shrink-0" :class="'dashboard-today-' + item.type">
                          <i class="bi" :class="item.type === 'task_in_scadenza' ? 'bi-clock' : item.type === 'task_scaduta' ? 'bi-exclamation-circle' : item.type === 'evento' ? 'bi-calendar3' : item.type === 'da_approvare' ? 'bi-check2-circle' : 'bi-chat-dots'"></i>
                        </div>
                        <div class="min-w-0 flex-grow-1">
                          <div class="fw-semibold text-truncate">[[ item.label ]]</div>
                          <div class="small text-secondary d-flex flex-wrap gap-2 mt-1">
                            <span v-if="item.time"><i class="bi bi-clock me-1"></i>[[ item.time ]]</span>
                            <span v-if="item.priority" v-html="priorityHtml(item.priority)"></span>
                            <span v-if="item.cliente"><i class="bi bi-person me-1"></i>[[ item.cliente ]]</span>
                          </div>
                        </div>
                        <i class="bi bi-chevron-right text-secondary flex-shrink-0 mt-1"></i>
                      </div>
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="row g-3 mt-3">
            <div class="col-12 col-xl-4">
              <article class="card h-100 rounded-3 border border-light-subtle">
                <div class="card-body p-3 p-md-4">
                  <h2 class="h5 mb-3">Prossimi eventi</h2>
                  <div v-if="!summary.upcoming_events || summary.upcoming_events.length === 0" class="text-secondary py-3 text-center">
                    <div class="dashboard-empty-icon"><i class="bi bi-calendar2-week"></i></div>
                    <div class="small">Nessun evento nei prossimi 7 giorni.</div>
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
                <div class="card-body p-3 p-md-4">
                  <h2 class="h5 mb-3">Prossime pubblicazioni</h2>
                  <div v-if="!summary.upcoming_publications || summary.upcoming_publications.length === 0" class="text-secondary py-3 text-center">
                    <div class="dashboard-empty-icon"><i class="bi bi-calendar2-week"></i></div>
                    <div class="small">Nessuna pubblicazione nei prossimi 7 giorni.</div>
                  </div>
                  <a v-for="pub in summary.upcoming_publications" :key="pub.id" :href="pub.url" class="dashboard-list-item">
                    <div class="d-flex align-items-start justify-content-between gap-2 mb-1">
                      <div class="fw-bold text-truncate min-w-0">[[ pub.title ]]</div>
                      <span v-html="badgeHtml('editorial_status', pub.status)" class="flex-shrink-0"></span>
                    </div>
                    <div class="small text-secondary d-flex flex-wrap gap-2">
                      <span><i class="bi bi-calendar3 me-1"></i>[[ formatDate(pub.date) ]]</span>
                      <span v-if="pub.cliente"><i class="bi bi-person me-1"></i>[[ pub.cliente.name ]]</span>
                    </div>
                  </a>
                </div>
              </article>
            </div>

            <div class="col-12 col-xl-4">
              <article class="card h-100 rounded-3 border border-light-subtle">
                <div class="card-body p-3 p-md-4">
                  <h2 class="h5 mb-3">Ultimi aggiornamenti</h2>
                  <div v-if="!summary.recent_updates || summary.recent_updates.length === 0" class="text-secondary py-3 text-center">
                    <div class="dashboard-empty-icon"><i class="bi bi-arrow-repeat"></i></div>
                    <div class="small">Nessun aggiornamento recente.</div>
                  </div>
                  <a v-for="upd in summary.recent_updates" :key="upd.url" :href="upd.url" class="dashboard-list-item">
                    <div class="d-flex align-items-start justify-content-between gap-2 mb-1">
                      <div class="fw-bold text-truncate min-w-0">[[ upd.label ]]</div>
                      <span v-html="badgeHtml(upd.type === 'task' ? 'task_status' : upd.type === 'preventivo' ? 'quote_status' : 'work_status', upd.status)" class="flex-shrink-0"></span>
                    </div>
                    <div class="small text-secondary">
                      <span v-if="upd.ts"><i class="bi bi-clock me-1"></i>[[ formatDateTime(upd.ts) ]]</span>
                    </div>
                  </a>
                </div>
              </article>
            </div>
          </div>

          <div class="mt-4">
            <div class="d-flex align-items-center justify-content-between mb-3">
              <h2 class="h5 mb-0">Finanze mese</h2>
              <a class="btn btn-sm btn-outline-primary" href="/finance">Apri finanze</a>
            </div>
            <div class="row g-3">
              <div class="col-6 col-md-3" v-for="card in financeCards" :key="card.title">
                <article class="card h-100 rounded-3 border border-light-subtle dashboard-kpi-card">
                  <div class="card-body p-3 p-md-4">
                    <div class="min-w-0">
                      <p class="text-secondary small mb-1 dashboard-kpi-label">[[ card.title ]]</p>
                      <div class="fw-bold text-truncate dashboard-kpi-value dashboard-kpi-finance" :class="card.valueClass">[[ card.value ]]</div>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </div>
        </div>
      </section>
    `,
  });

  erpDashboardApp.mount("#app");
}

