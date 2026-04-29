const TabellaClienti = {
  props: ["clienti_data"],
  template: `
    <table class="table my-0 sortable table-hover rounded-3 p-2 no-last-border erp-table">
      <thead>
        <tr>
          <th class="fw-bold pointer col-cliente" scope="col">Nominativo</th>
          <th title="Quantita di lavori del cliente" class="fw-bold text-center pointer col-id" scope="col">Qty</th>
          <th class="fw-bold pointer" scope="col">Email</th>
          <th class="fw-bold pointer col-date" scope="col">Telefono</th>
          <th class="fw-bold pointer text-center col-note" scope="col">Note</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="clienti_data.length > 0">
          <tr v-for="cliente in clienti_data">
            <td>
              <a class="fw-bold text-decoration-none" :href="'/clienti/' + cliente.id">
                <i :style="{ color: cliente.colore }" class="bi bi-person-circle me-2"></i>[[ cliente.nome ]]
              </a>
            </td>
            <td class="text-center">[[ cliente.count_lavori ]]</td>
            <td>[[ cliente.email ]]</td>
            <td>[[ cliente.telefono ]]</td>
            <td class="text-center" v-html="renderNoteIcon(cliente.note)"></td>
          </tr>
        </template>
        <tr v-else>
          <td colspan="5" class="text-center">Nessun cliente trovato.</td>
        </tr>
      </tbody>
    </table>
  `,
  methods: {
    initTooltips() {
      Vue.nextTick(() => {
        document
          .querySelectorAll('#clientiPage [data-bs-toggle="tooltip"]')
          .forEach((el) => {
            if (!bootstrap.Tooltip.getInstance(el)) {
              new bootstrap.Tooltip(el);
            }
          });
      });
    },
    truncateNote(note) {
      if (!note) return "";
      const clean = String(note).replace(/\s+/g, " ").trim();
      return clean.length > 100 ? `${clean.slice(0, 100)}...` : clean;
    },
    escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    },
    renderNoteIcon(note) {
      if (!note) return "-";
      const title = this.escapeHtml(this.truncateNote(note));
      return `<i data-bs-placement="left" data-bs-toggle="tooltip" data-bs-title="${title}" class="bi bi-stickies" style="font-size: 1rem; color: #7e508d !important;"></i>`;
    },
  },
  mounted() {
    this.initTooltips();
  },
  updated() {
    this.initTooltips();
  },
  delimiters: ["[[", "]]"],
};
