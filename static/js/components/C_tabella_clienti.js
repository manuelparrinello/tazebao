const TabellaClienti = {
  props: ["clienti_data"],
  template: `
    <table class="table erp-table my-0 d-none d-md-table">
      <thead>
        <tr>
          <th class="fw-bold pointer col-nominativo" scope="col">Nominativo</th>
          <th class="fw-bold pointer col-email" scope="col">Contatti</th>
          <th class="fw-bold pointer col-date" scope="col">Citt&agrave;</th>
          <th class="fw-bold pointer col-status" scope="col">P.IVA</th>
          <th class="fw-bold pointer col-payment" scope="col">PEC / SDI</th>
          <th class="fw-bold pointer text-center col-note" scope="col">Note</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="clienti_data.length > 0">
          <tr v-for="cliente in clienti_data">
            <td>
              <a class="fw-bold text-decoration-none d-flex align-items-center gap-2" :href="'/clienti/' + cliente.id" :title="cliente.nome">
                <i :style="{ color: cliente.colore }" class="bi bi-person-circle flex-shrink-0"></i>
                <span class="text-truncate">[[ cliente.nome ]]</span>
              </a>
            </td>
            <td>
              <div v-if="cliente.email" class="text-truncate">[[ cliente.email ]]</div>
              <small v-if="cliente.telefono" class="text-secondary d-block text-truncate">[[ cliente.telefono ]]</small>
              <span v-if="!cliente.email && !cliente.telefono" class="text-secondary">-</span>
            </td>
            <td>[[ cliente.citta || '-' ]]</td>
            <td>[[ cliente.p_iva || '-' ]]</td>
            <td>
              <template v-if="cliente.pec || cliente.sdi">
                <div v-if="cliente.pec" class="text-truncate">[[ cliente.pec ]]</div>
                <small v-if="cliente.sdi" class="text-secondary d-block text-truncate">SDI: [[ cliente.sdi ]]</small>
              </template>
              <span v-else class="text-secondary">-</span>
            </td>
            <td class="text-center" v-html="renderNoteIcon(cliente.note)"></td>
          </tr>
        </template>
        <tr v-else>
          <td colspan="6" class="text-center">Nessun cliente trovato.</td>
        </tr>
      </tbody>
    </table>
    <div class="mobile-list d-md-none">
      <template v-if="clienti_data.length > 0">
        <a v-for="cliente in clienti_data" :key="cliente.id" class="mobile-list-item mobile-row-link" :href="'/clienti/' + cliente.id">
          <div class="d-flex align-items-start justify-content-between gap-3">
            <div class="min-w-0 flex-grow-1">
              <div class="d-flex align-items-center gap-2 mb-1">
                <i :style="{ color: cliente.colore }" class="bi bi-person-circle flex-shrink-0"></i>
                <span class="fw-bold mobile-row-title">[[ cliente.nome ]]</span>
              </div>
              <div class="mobile-row-meta">
                <span v-if="cliente.email" class="mobile-row-muted">
                  <i class="bi bi-envelope me-1"></i>[[ cliente.email ]]
                </span>
                <span v-if="cliente.telefono" class="mobile-row-muted ms-2">
                  <i class="bi bi-telephone me-1"></i>[[ cliente.telefono ]]
                </span>
              </div>
              <div v-if="cliente.citta" class="mobile-row-muted mt-1">
                <i class="bi bi-geo-alt me-1"></i>[[ cliente.citta ]]
              </div>
            </div>
            <i class="bi bi-chevron-right text-secondary flex-shrink-0 mt-1"></i>
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
