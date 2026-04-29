const TabellaClienti = {
  props: ["clienti_data"],
  template: `
    <table class="table my-0 sortable table-hover rounded-3 p-2 no-last-border erp-table d-none d-md-table">
      <thead>
        <tr>
          <th class="fw-bold pointer col-nominativo" scope="col">Nominativo</th>
          <th class="fw-bold pointer col-email mobile-hide" scope="col">Email</th>
          <th class="fw-bold pointer col-date mobile-hide" scope="col">Telefono</th>
          <th class="fw-bold pointer text-center col-note" scope="col">Note</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="clienti_data.length > 0">
          <tr v-for="cliente in clienti_data">
            <td>
              <a class="fw-bold text-decoration-none d-block text-truncate" :href="'/clienti/' + cliente.id" :title="cliente.nome">
                <i :style="{ color: cliente.colore }" class="bi bi-person-circle me-2"></i>[[ cliente.nome ]]
              </a>
            </td>
            <td class="text-nowrap mobile-hide">[[ cliente.email ]]</td>
            <td class="mobile-hide">[[ cliente.telefono ]]</td>
            <td class="text-center" v-html="renderNoteIcon(cliente.note)"></td>
          </tr>
        </template>
        <tr v-else>
          <td colspan="4" class="text-center">Nessun cliente trovato.</td>
        </tr>
      </tbody>
    </table>
    <div class="mobile-list d-md-none">
      <template v-if="clienti_data.length > 0">
        <a v-for="cliente in clienti_data" :key="cliente.id" class="mobile-list-item mobile-row-link" :href="'/clienti/' + cliente.id">
          <div class="d-flex align-items-center justify-content-between gap-3">
            <div class="d-flex align-items-center gap-2 min-w-0">
              <i :style="{ color: cliente.colore }" class="bi bi-person-circle flex-shrink-0"></i>
              <span class="fw-bold mobile-row-title" :title="cliente.nome">[[ cliente.nome ]]</span>
            </div>
            <i class="bi bi-chevron-right text-secondary flex-shrink-0"></i>
          </div>
        </a>
      </template>
      <div v-else class="text-center text-secondary py-4">
        Nessun cliente trovato.
      </div>
    </div>
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
