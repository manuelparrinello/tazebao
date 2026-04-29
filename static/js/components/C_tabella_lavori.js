const TabellaLavori = {
  props: {
    lavori_data: Array,
    stato_lavori: Array,
    update_status: Function,
    filtro_stati: Function,
  },
  template: `
    <table class="table sortable my-0 table-hover rounded-3 no-last-border erp-table d-none d-md-table" id="tabellaLavori">
      <thead>
        <tr>
          <th class="fw-bold pointer text-center col-prio" scope="col">Prio</th>
          <th class="fw-bold pointer col-desc" scope="col">Descrizione</th>
          <th class="fw-bold pointer col-money text-end" scope="col">Prezzo</th>
          <th class="fw-bold pointer col-cliente mobile-hide" scope="col">Cliente</th>
          <th class="fw-bold pointer text-center col-payment mobile-hide" scope="col">Pagamento</th>
          <th class="fw-bold pointer text-center col-note mobile-hide" scope="col">Note</th>
          <th class="fw-bold pointer text-center col-status" scope="col">Stato</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="lavori_data.length > 0">
          <tr v-for="lavoro in lavori_data">
            <td :sorttable_customkey="prioIndex(lavoro.priorita)" class="text-center col-prio">
              <span v-html="prioPill(lavoro.priorita)" :class="prioClass(lavoro.priorita)"></span>
            </td>
            <td>
              <a class="fw-bold text-decoration-underline" :href="'/lavori/' + lavoro.id">[[ lavoro.descrizione ]]</a>
            </td>
            <td :sorttable_customkey="lavoro.preventivato" class="text-end">[[ lavoro.preventivato ]] &euro;</td>
            <td class="mobile-hide">
              <i :style="{ color: lavoro.cliente.colore }" class="bi bi-person-circle me-2"></i>
              <a :href="'/clienti/' + lavoro.cliente.id" class="text-decoration-none a-no-color">[[ lavoro.cliente.name ]]</a>
            </td>
            <td class="text-center mobile-hide">[[ lavoro.data_pagamento || '-' ]]</td>
            <td class="text-center mobile-hide" id="note_td" v-html="renderNoteIcon(lavoro.note)"></td>
            <td class="text-center">
              <template v-if="canMutate()">
                <select :class="statusColor(lavoro.stato)" @change="update_status($event, lavoro.id)" :id="'status_select_' + lavoro.id" name="status_select" class="form-control form-select form-select-sm status-select">
                  <option :value="lavoro.stato" selected>[[ lavoro.stato ]]</option>
                  <option v-for="stato in filtro_stati(lavoro.stato)" :value="stato">[[ stato ]]</option>
                </select>
              </template>
              <template v-else>
                <span class="badge rounded-pill bg-primary">[[ lavoro.stato ]]</span>
              </template>
            </td>
          </tr>
        </template>
        <tr v-else>
          <td colspan="7" class="text-center">Nessun lavoro trovato.</td>
        </tr>
      </tbody>
    </table>
    <div class="mobile-list d-md-none">
      <template v-if="lavori_data.length > 0">
        <a v-for="lavoro in lavori_data" :key="lavoro.id" class="mobile-list-item mobile-row-link" :href="'/lavori/' + lavoro.id">
          <div class="d-flex align-items-start justify-content-between gap-3">
            <div class="min-w-0">
              <div class="d-flex align-items-center gap-2 mb-1">
                <span class="fw-bold mobile-row-title" :title="lavoro.descrizione">[[ lavoro.descrizione ]]</span>
                <span class="badge rounded-pill text-bg-primary flex-shrink-0">[[ lavoro.stato ]]</span>
              </div>
            </div>
            <i class="bi bi-chevron-right text-secondary flex-shrink-0"></i>
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
    prioPill(prio) {
      if (prio === "Bassa") return `<i class="bi bi-emoji-smile"></i>`;
      if (prio === "Media") return `<i class="bi bi-emoji-neutral"></i>`;
      if (prio === "Alta") return `<i class="bi bi-emoji-angry"></i>`;
      return "";
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

    prioClass(prio) {
      if (prio === "Bassa") return "prio-low";
      if (prio === "Media") return "prio-med";
      if (prio === "Alta") return "prio-high";
      return "";
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
