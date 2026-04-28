/*--------------------*/
/*  CANCELLA CLIENTE  */
/*--------------------*/
function deleteCliente(id) {
  return fetch(`/clienti/${id}`, {
    method: "delete",
    headers: {
      Accept: "application/json",
    },
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
    headers: {
      Accept: "application/json",
    },
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
          { title: "Eventi prossimi", value: this.summary.upcoming_events_count, icon: "bi-calendar-event" },
          { title: "Clienti", value: this.summary.active_clients_count, icon: "bi-people" },
          { title: "Lavori attivi", value: this.summary.active_jobs_count, icon: "bi-briefcase" },
          { title: "Preventivi bozza", value: this.summary.draft_quotes_count, icon: "bi-file-earmark-text" },
          { title: "Preventivi accettati", value: this.summary.accepted_quotes_count, icon: "bi-check2-circle" },
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
        if (!value) return "-";
        return new Intl.DateTimeFormat("it-IT", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        }).format(new Date(value));
      },
      formatDateTime(value) {
        if (!value) return "-";
        return new Intl.DateTimeFormat("it-IT", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }).format(new Date(value));
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

        <div v-if="loading" class="d-flex align-items-center justify-content-center" style="min-height: 360px;">
          <span class="loader"></span>
        </div>

        <div v-else-if="error" class="alert alert-danger d-flex align-items-center justify-content-between gap-3">
          <span>[[ error ]]</span>
          <button class="btn btn-sm btn-outline-danger" type="button" @click="loadDashboard">Riprova</button>
        </div>

        <div v-else>
          <div class="row g-4">
            <div class="col-12 col-md-6 col-xl-3" v-for="card in kpiCards" :key="card.title">
              <article class="card h-100 border-0 shadow-sm">
                <div class="card-body p-4">
                  <div class="d-flex align-items-start justify-content-between gap-3">
                    <div>
                      <p class="text-secondary small mb-2">[[ card.title ]]</p>
                      <div class="display-6 fw-bold">[[ card.value ]]</div>
                    </div>
                    <div class="rounded-3 bg-primary text-white d-inline-flex align-items-center justify-content-center flex-shrink-0" style="width: 44px; height: 44px;">
                      <i class="bi" :class="card.icon"></i>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div class="row g-4 mt-1">
            <div class="col-12 col-xl-4">
              <article class="card h-100 border-0 shadow-sm">
                <div class="card-body p-4">
                  <h2 class="h5 mb-3">Prossimi eventi</h2>
                  <div v-if="summary.upcoming_events.length === 0" class="text-secondary">Nessun evento nei prossimi 7 giorni.</div>
                  <a v-for="event in summary.upcoming_events" :key="event.id" :href="event.url" class="d-block border-bottom py-3 text-dark">
                    <div class="fw-bold">[[ event.title ]]</div>
                    <div class="small text-secondary">[[ formatDateTime(event.start_datetime) ]] · [[ labelize(event.event_type) ]]</div>
                    <div v-if="event.cliente" class="small text-secondary">[[ event.cliente.name ]]</div>
                  </a>
                </div>
              </article>
            </div>

            <div class="col-12 col-xl-4">
              <article class="card h-100 border-0 shadow-sm">
                <div class="card-body p-4">
                  <h2 class="h5 mb-3">Task recenti</h2>
                  <div v-if="summary.recent_tasks.length === 0" class="text-secondary">Nessuna task presente.</div>
                  <a v-for="task in summary.recent_tasks" :key="task.id" :href="task.url" class="d-block border-bottom py-3 text-dark">
                    <div class="fw-bold">[[ task.name ]]</div>
                    <div class="small text-secondary">[[ labelize(task.status) ]] · [[ labelize(task.priority) ]]</div>
                    <div class="small" :class="task.due_date ? 'text-secondary' : 'text-muted'">Scadenza: [[ formatDate(task.due_date) ]]</div>
                  </a>
                </div>
              </article>
            </div>

            <div class="col-12 col-xl-4">
              <article class="card h-100 border-0 shadow-sm">
                <div class="card-body p-4">
                  <h2 class="h5 mb-3">Preventivi recenti</h2>
                  <div v-if="summary.recent_quotes.length === 0" class="text-secondary">Nessun preventivo presente.</div>
                  <a v-for="quote in summary.recent_quotes" :key="quote.id" :href="quote.url" class="d-block border-bottom py-3 text-dark">
                    <div class="fw-bold">[[ quote.descrizione ]]</div>
                    <div class="small text-secondary">[[ quote.cliente ? quote.cliente.name : '-' ]] · [[ labelize(quote.stato) ]]</div>
                    <div class="small text-secondary">[[ formatDate(quote.data_creazione) ]] · [[ formatCurrency(quote.totale_preventivo) ]]</div>
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
