const TabellaLavori = {
  props: {
    lavori_data: Array,
    stato_lavori: Array,
    update_status: Function,
    filtro_stati: Function,
  },
  template: `
    <table class="table sortable my-0 table-hover rounded-3 no-last-border lavori-table d-none d-md-table" id="tabellaLavori">
      <thead>
        <tr>
          <th class="fw-bold pointer text-center col-prio" scope="col">Prio</th>
          <th class="fw-bold pointer col-title" scope="col">Descrizione</th>
          <th class="fw-bold pointer col-cliente mobile-hide" scope="col">Cliente</th>
          <th class="fw-bold pointer col-money text-end" scope="col">Prezzo</th>
          <th class="fw-bold pointer text-center col-payment mobile-hide" scope="col">Pagamento</th>
          <th class="fw-bold pointer text-center col-note mobile-hide" scope="col">Note</th>
          <th class="fw-bold pointer text-center col-pdf" scope="col">PDF</th>
          <th class="fw-bold pointer text-center col-status" scope="col">Stato</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="lavori_data.length > 0">
          <tr v-for="lavoro in lavori_data">
            <td :sorttable_customkey="prioIndex(lavoro.priorita)" class="text-center col-prio">
                <span v-html="priorityHtml(lavoro.priorita)"></span>
            </td>
            <td>
              <a class="fw-bold text-decoration-underline" :href="'/lavori/' + lavoro.id">[[ lavoro.descrizione ]]</a>
            </td>
            <td class="mobile-hide">
              <span class="cliente-bullet" :style="{ backgroundColor: lavoro.cliente.colore || '#adb5bd' }"></span>
              <a :href="'/clienti/' + lavoro.cliente.id" class="text-decoration-none a-no-color">[[ lavoro.cliente.name ]]</a>
            </td>
            <td :sorttable_customkey="lavoro.preventivato" class="text-end">[[ lavoro.preventivato ]] &euro;</td>
            <td class="text-center mobile-hide">[[ formatDate(lavoro.data_pagamento) ]]</td>
            <td class="text-center mobile-hide note-td" v-html="renderNoteIcon(lavoro.note)"></td>
            <td class="text-center col-pdf" v-html="pdfIcon(lavoro.preventivo_pdf_path)"></td>
            <td class="text-center">
              <template v-if="canMutate()">
                <select :class="statusColor(lavoro.stato)" @change="update_status($event, lavoro.id)" :id="'status_select_' + lavoro.id" name="status_select" class="form-control form-select form-select-sm status-select">
                  <option :value="lavoro.stato" selected>[[ lavoro.stato ]]</option>
                  <option v-for="stato in filtro_stati(lavoro.stato)" :value="stato">[[ stato ]]</option>
                </select>
              </template>
              <template v-else>
                <span v-html="badgeHtml('work_status', lavoro.stato)"></span>
              </template>
            </td>
          </tr>
        </template>
        <tr v-else>
          <td colspan="8" class="text-center">Nessun lavoro trovato.</td>
        </tr>
      </tbody>
    </table>
    <div class="mobile-list d-md-none">
      <template v-if="lavori_data.length > 0">
        <a v-for="lavoro in lavori_data" :key="lavoro.id" class="mobile-list-item mobile-row-link" :href="'/lavori/' + lavoro.id">
          <div class="d-flex align-items-start justify-content-between gap-3">
            <div class="min-w-0">
              <div class="fw-bold mobile-row-title mb-1" :title="lavoro.descrizione">[[ lavoro.descrizione ]]</div>
              <div class="d-flex flex-wrap gap-1 mb-1">
                <span v-html="badgeHtml('work_status', lavoro.stato)"></span>
              <span v-html="priorityHtml(lavoro.priorita)"></span>
              </div>
              <div class="mobile-row-muted">
                <template v-if="lavoro.cliente">
                  <span><i class="bi bi-person me-1"></i>[[ lavoro.cliente.name ]]</span>
                </template>
                <template v-if="lavoro.preventivato > 0">
                  <span class="ms-2"><i class="bi bi-currency-euro me-1"></i>[[ lavoro.preventivato ]]</span>
                </template>
                <span v-if="lavoro.preventivo_pdf_path" class="ms-2 text-success">
                  <i class="bi bi-file-earmark-pdf-fill me-1"></i>PDF
                </span>
              </div>
            </div>
            <i class="bi bi-chevron-right text-secondary flex-shrink-0 mt-1"></i>
          </div>
        </a>
      </template>
      <div v-else class="text-center text-secondary py-4">
        Nessun lavoro trovato.
      </div>
    </div>
  `,
  methods: {
    canMutate() {
      return window.erpCanMutate !== false;
    },
    badgeHtml(kind, value, text = null) {
      return window.erpBadge?.html ? window.erpBadge.html(kind, value, text) : `<span class="badge rounded-pill">${value || "-"}</span>`;
    },
    priorityHtml(prio) {
      if (!prio) return '-';
      const label = String(prio).replace(/\b\w/g, c => c.toUpperCase());
      return `<span class="priority-indicator priority-${prio.toLowerCase()}"><span class="priority-dot"></span><span class="priority-label">${label}</span></span>`;
    },
    formatDate(value) {
      const formatter = window.erpDateFormatter?.formatDate;
      if (formatter) return formatter(value);
      if (!value) return "-";
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) return "-";
      const parts = new Intl.DateTimeFormat("it-IT", {
        day: "numeric",
        month: "long",
        year: "numeric",
      }).formatToParts(parsed);
      return parts
        .map((part) => (part.type === "month" ? part.value.charAt(0).toUpperCase() + part.value.slice(1) : part.value))
        .join("");
    },
    statusColor(stato) {
      if (stato === "Da iniziare") return "selectDaIniziare";
      if (stato === "In corso") return "selectInCorso";
      if (stato === "In attesa") return "selectInAttesa";
      return "selectCompletato";
    },

    prioIndex(prio) {
      if (prio === "Bassa") return 1;
      if (prio === "Media") return 2;
      if (prio === "Alta") return 3;
      return "";
    },

    pdfIcon(path) {
      if (path) {
        return '<span class="lavoro-pdf-icon text-success"><i class="bi bi-file-earmark-pdf-fill"></i></span>';
      }
      return '<span class="lavoro-pdf-icon text-secondary">&mdash;</span>';
    },
    renderNoteIcon(note) {
      if (note) {
        return `<i data-bs-placement="left" data-bs-toggle="tooltip" data-bs-title="${note}" class="bi bi-stickies" style="font-size: 1rem; color: #7e508d !important;"></i>`;
      }
      return "-";
    },
  },
  delimiters: ["[[", "]]"],
};
