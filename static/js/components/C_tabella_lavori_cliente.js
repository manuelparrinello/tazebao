const TabellaLavori = {
  props: ["lavori_data"], // Qui dichiari il nome del "tubo". "lavori_data" sostituisce nell'HTML sotto l'oggetto restituito dalla fetch. In questo caso cliente.lavori 
  template: `
     <table class="table sortable table-hover mt-2" id="tabellaLavori">
                <thead>
                    <tr>
                        <th class="pointer col-desc" scope="col">Descrizione</th>
                        <th class="pointer text-center" scope="col">Preventivato</th>
                        <th class="pointer text-center" scope="col">Priorità</th>
                        <th class="pointer text-center" scope="col">Stato</th>
                        <th class="pointer text-center" scope="col">Data inizio</th>
                        <th class="pointer text-center" scope="col">Data fine</th>
                        <th class="pointer text-center" scope="col">Data pagamento</th>
                        <th class="pointer col-note text-center" scope="col">Note</th>

                    </tr>
                </thead>
                <tbody>
                    <template v-if="lavori_data.length > 0">
                        <tr v-for="lavoro in lavori_data">
                            <td class="fw-bold">[[ lavoro.descrizione ]]</td>
                            <td class="text-center">[[ lavoro.preventivato ]]€</td>
                            <td class="text-center">
                                <span class="prio-pill" :class="prioClass(lavoro.priorita)">
                                    [[ lavoro.priorita ]]
                                </span>
                            </td>
                            <td class="text-center">[[ lavoro.stato || '-' ]]</td>
                            <td class="text-center">[[ lavoro.data_inizio || '-' ]]</td>
                            <td class="text-center">[[ lavoro.data_fine || "-" ]]</td>
                            <td class="text-center">[[ lavoro.data_pagamento || "-" ]]</td>
                            <td class="text-center" v-html="renderNoteIcon(lavoro.note)">[[ lavoro.note || "-" ]]</td>
                        </tr>
                    </template>
                    <tr v-else>
                        <td colspan="9" class="text-center">Nessun lavoro associato al cliente.</td>
                    </tr>
                </tbody>
            </table>
    `,
  methods: {
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
