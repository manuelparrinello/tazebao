const TabellaLavori = {
  props: {
    lavori_data: Array,
    stato_lavori: Array,
    update_status: Function,
    filtro_stati: Function,
  },
  template: `
    <table class="table sortable my-0 table-hover rounded-3 no-last-border erp-table" id="tabellaLavori">
      <thead>
        <tr>
          <th class="fw-bold pointer text-center col-prio" scope="col">Prio</th>
          <th class="fw-bold pointer col-desc" scope="col">Descrizione</th>
          <th class="fw-bold pointer col-money text-end" scope="col">Prezzo</th>
          <th class="fw-bold pointer col-cliente" scope="col">Cliente</th>
          <th class="fw-bold pointer text-center col-payment" scope="col">Pagamento</th>
          <th class="fw-bold pointer text-center col-note" scope="col">Note</th>
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
            <td>
              <i :style="{ color: lavoro.cliente.colore }" class="bi bi-person-circle me-2"></i>
              <a :href="'/clienti/' + lavoro.cliente.id" class="text-decoration-none a-no-color">[[ lavoro.cliente.name ]]</a>
            </td>
            <td class="text-center">[[ lavoro.data_pagamento || '-' ]]</td>
            <td class="text-center" id="note_td" v-html="renderNoteIcon(lavoro.note)"></td>
            <td class="text-center">
              <select :class="statusColor(lavoro.stato)" @change="update_status($event, lavoro.id)" :id="'status_select_' + lavoro.id" name="status_select" class="form-control form-select form-select-sm status-select">
                <option :value="lavoro.stato" selected>[[ lavoro.stato ]]</option>
                <option v-for="stato in filtro_stati(lavoro.stato)" :value="stato">[[ stato ]]</option>
              </select>
            </td>
          </tr>
        </template>
        <tr v-else>
          <td colspan="7" class="text-center">Nessun lavoro trovato.</td>
        </tr>
      </tbody>
    </table>
  `,
  methods: {
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
